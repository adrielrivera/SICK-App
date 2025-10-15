#!/usr/bin/env python3
"""
SICK Capstone - Combined PBT Sensor Web App with GPIO Pulse Output
Real-time waveform visualization + GPIO pulse generation
"""
import time
import sys
from threading import Thread, Lock
from collections import deque
import serial
import pigpio
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from config import *

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Shared data buffers
data_lock = Lock()
raw_buffer = deque(maxlen=BUFFER_SIZE)
env_buffer = deque(maxlen=BUFFER_SIZE)
time_buffer = deque(maxlen=BUFFER_SIZE)

# Serial connection
ser = None
serial_running = False

# GPIO connection
pi = None
GPIO_PULSE = 18

# Statistics
baseline = 0.0
envelope = 0.0
sample_count = 0

# Peak detection state
armed = True
peak = 0.0
cap_end = 0.0

# GPIO pulse parameters (from pbt_pulse_plot.py)
CAPTURE_MS = 250
REFRACTORY_MS = 200
A_MIN, A_MAX = 80, 700
W_MIN_MS, W_MAX_MS = 60, 1500
REARM_LEVEL = TRIGGER_THRESHOLD * 0.4

# Statistics for pulse generation
pulse_count = 0


def clamp(x, lo, hi):
    """Clamp value between min and max."""
    return max(lo, min(hi, x))


def map_linear(x, x0, x1, y0, y1):
    """Map value from one range to another."""
    if x1 <= x0:
        return y0
    t = (x - x0) / (x1 - x0)
    return y0 + t * (y1 - y0)


def build_pulse_wave(pi, gpio, width_ms):
    """Build a pulse waveform for pigpio."""
    pi.write(gpio, 0)
    pi.wave_clear()
    up = pigpio.pulse(gpio_on=1<<gpio, gpio_off=0, delay=int(width_ms*1000))
    dn = pigpio.pulse(gpio_on=0, gpio_off=1<<gpio, delay=1)
    pi.wave_add_generic([up, dn])
    return pi.wave_create()


def read_one_int(ser):
    """Read one line and parse int; return None on empty/invalid."""
    try:
        s = ser.readline().decode(errors="ignore").strip()
        if not s:
            return None
        return int(s)
    except (ValueError, UnicodeDecodeError):
        return None


def serial_reader_thread():
    """
    Background thread to read serial data and update buffers.
    Also handles GPIO pulse generation based on detected peaks.
    """
    global ser, serial_running, baseline, envelope, sample_count
    global pi, armed, peak, cap_end, pulse_count
    
    print("Initializing pigpio daemon connection...")
    pi = pigpio.pi()
    if not pi.connected:
        print("WARNING: pigpio daemon not running. GPIO pulses disabled.", file=sys.stderr)
        print("Run: sudo systemctl start pigpiod", file=sys.stderr)
        pi = None
    else:
        pi.set_mode(GPIO_PULSE, pigpio.OUTPUT)
        pi.write(GPIO_PULSE, 0)
        print(f"GPIO {GPIO_PULSE} initialized for pulse output")
    
    print("Initializing serial connection...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
        time.sleep(0.2)
        ser.reset_input_buffer()
    except Exception as e:
        print(f"ERROR: Could not open serial port {SERIAL_PORT}: {e}", file=sys.stderr)
        serial_running = False
        if pi:
            pi.stop()
        return
    
    # Quick baseline warm-up (200 ms)
    baseline_samples = []
    t0 = time.time()
    while time.time() - t0 < 0.2:
        v = read_one_int(ser)
        if v is not None:
            baseline_samples.append(v)
    
    if baseline_samples:
        baseline = sum(baseline_samples) / len(baseline_samples)
    else:
        baseline = 40.0
    
    envelope = 0.0
    print(f"Baseline calibrated: {baseline:.1f} ADC counts")
    
    # Main reading loop
    start_time = time.time()
    sample_count = 0
    last_emit = time.time()
    emit_interval = EMIT_INTERVAL  # Emit data at configured rate
    
    batch_raw = []
    batch_env = []
    batch_time = []
    
    while serial_running:
        v = read_one_int(ser)
        if v is None:
            time.sleep(0.001)
            continue
        
        sample_count += 1
        current_time = time.time() - start_time
        
        # Update baseline and envelope
        baseline = (1 - BASELINE_ALPHA) * baseline + BASELINE_ALPHA * v
        xmag = abs(v - baseline)
        envelope = (1 - ENVELOPE_ALPHA) * envelope + ENVELOPE_ALPHA * xmag
        
        # Store in batch for emission
        batch_raw.append(v)
        batch_env.append(envelope)
        batch_time.append(current_time)
        
        # ============================================================
        # GPIO PULSE GENERATION LOGIC (from pbt_pulse_plot.py)
        # ============================================================
        if pi:
            now = time.time()
            
            if armed:
                # Check for trigger
                if envelope > TRIGGER_THRESHOLD:
                    armed = False
                    peak = envelope
                    cap_end = now + (CAPTURE_MS / 1000.0)
            else:
                # Capture peak during capture window
                if envelope > peak:
                    peak = envelope
                
                # Check if capture window ended or envelope dropped
                if now >= cap_end or envelope < (TRIGGER_THRESHOLD * 0.5):
                    # Map amplitude to pulse width and fire pulse
                    a_clamped = clamp(peak, A_MIN, A_MAX)
                    width_ms = clamp(
                        map_linear(a_clamped, A_MIN, A_MAX, W_MIN_MS, W_MAX_MS),
                        W_MIN_MS, W_MAX_MS
                    )
                    
                    pulse_count += 1
                    print(f"Pulse #{pulse_count}: Peak={peak:.1f} → {width_ms:.0f} ms")
                    
                    # Generate pulse
                    wid = build_pulse_wave(pi, GPIO_PULSE, width_ms)
                    if wid >= 0:
                        pi.wave_send_once(wid)
                        while pi.wave_tx_busy():
                            time.sleep(0.001)
                        pi.wave_delete(wid)
                    else:
                        pi.write(GPIO_PULSE, 1)
                        time.sleep(width_ms / 1000.0)
                        pi.write(GPIO_PULSE, 0)
                    
                    # Refractory period
                    t_ref_end = time.time() + (REFRACTORY_MS / 1000.0)
                    while time.time() < t_ref_end:
                        v2 = read_one_int(ser)
                        if v2 is None:
                            continue
                        sample_count += 1
                        baseline = (1 - BASELINE_ALPHA) * baseline + BASELINE_ALPHA * v2
                        xmag = abs(v2 - baseline)
                        envelope = (1 - ENVELOPE_ALPHA) * envelope + ENVELOPE_ALPHA * xmag
                    
                    # Wait to re-arm until envelope falls below REARM_LEVEL
                    while True:
                        if envelope < REARM_LEVEL:
                            armed = True
                            break
                        v3 = read_one_int(ser)
                        if v3 is None:
                            time.sleep(0.001)
                            continue
                        sample_count += 1
                        baseline = (1 - BASELINE_ALPHA) * baseline + BASELINE_ALPHA * v3
                        xmag = abs(v3 - baseline)
                        envelope = (1 - ENVELOPE_ALPHA) * envelope + ENVELOPE_ALPHA * xmag
        
        # ============================================================
        # EMIT DATA TO WEB CLIENTS
        # ============================================================
        now = time.time()
        if now - last_emit >= emit_interval:
            with data_lock:
                raw_buffer.extend(batch_raw)
                env_buffer.extend(batch_env)
                time_buffer.extend(batch_time)
            
            # Emit to all connected clients
            socketio.emit('sensor_data', {
                'raw': batch_raw,
                'envelope': batch_env,
                'time': batch_time,
                'baseline': baseline,
                'threshold': TRIGGER_THRESHOLD,
                'pulse_count': pulse_count
            })
            
            batch_raw = []
            batch_env = []
            batch_time = []
            last_emit = now
    
    # Cleanup
    if ser:
        ser.close()
    if pi:
        pi.write(GPIO_PULSE, 0)
        pi.stop()
    print("Serial reader thread stopped")


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('Client connected')
    
    # Send initial buffer data
    with data_lock:
        emit('initial_data', {
            'raw': list(raw_buffer),
            'envelope': list(env_buffer),
            'time': list(time_buffer),
            'baseline': baseline,
            'threshold': TRIGGER_THRESHOLD,
            'pulse_count': pulse_count
        })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')


@socketio.on('request_stats')
def handle_stats_request():
    """Send current statistics to client."""
    emit('stats', {
        'sample_count': sample_count,
        'baseline': baseline,
        'envelope': envelope,
        'buffer_size': len(raw_buffer),
        'pulse_count': pulse_count
    })


def start_serial_thread():
    """Start the serial reader thread."""
    global serial_running
    serial_running = True
    thread = Thread(target=serial_reader_thread, daemon=True)
    thread.start()
    return thread


if __name__ == '__main__':
    print("=" * 60)
    print("SICK PBT Sensor - Combined Web App + GPIO Pulse Output")
    print("=" * 60)
    print(f"Serial port: {SERIAL_PORT} @ {BAUD} baud")
    print(f"Samples per second: {SAMPLES_PER_SEC}")
    print(f"GPIO pulse output: Pin {GPIO_PULSE}")
    print(f"Trigger threshold: {TRIGGER_THRESHOLD} ADC counts")
    print(f"Web server: http://{HOST}:{PORT}")
    print("=" * 60)
    
    # Start serial reader thread (includes GPIO pulse generation)
    start_serial_thread()
    
    try:
        # Run Flask app
        socketio.run(app, host=HOST, port=PORT, debug=DEBUG)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        serial_running = False
        if ser:
            ser.close()
        if pi:
            pi.write(GPIO_PULSE, 0)
            pi.stop()

