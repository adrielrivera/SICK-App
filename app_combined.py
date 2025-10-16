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
# import pigpio  # No longer needed - using Arduino GPIO control
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

# GPIO control now handled by Arduino via Serial commands
# No Pi GPIO needed - Arduino controls arcade motherboard pins directly

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
A_MIN, A_MAX = 60, 85
W_MIN_MS, W_MAX_MS = 10, 1500
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


def map_linear_inverse(x, x0, x1, y0, y1):
    """Map value from one range to another INVERSELY (high x → low y)."""
    if x1 <= x0:
        return y1
    t = (x - x0) / (x1 - x0)
    return y1 - t * (y1 - y0)  # Inverted: subtract instead of add


def arcade_button_press(ser, duration_ms):
    """
    Arcade button press protocol using Arduino GPIO control.
    
    Sends commands to Arduino which controls the arcade motherboard pins.
    Arduino Pin 6: Active HIGH (normally LOW) - Press start signal
    Arduino Pin 5: Active LOW (normally HIGH) - Press confirmation signal
    
    Sequence:
    1. Send PIN6_HIGH command to Arduino
    2. Wait for duration_ms (THE PULSE - arcade measures this gap)
    3. Send PIN5_LOW command to Arduino
    4. Hold active state, then reset
    
    The arcade measures the time between Pin 6↑ and Pin 5↓
    """
    try:
        # Step 1: Pin 6 HIGH (press start signal) - 5V output from Arduino
        ser.write(b"PIN6_HIGH\n")
        ser.flush()  # Ensure command is sent immediately
        
        # Step 2: Wait for the mapped duration
        # This is THE PULSE that arcade measures (Pin 6 HIGH to Pin 5 LOW)
        time.sleep(duration_ms / 1000.0)
        
        # Step 3: Pin 5 LOW (press confirmed) - 0V output from Arduino
        ser.write(b"PIN5_LOW\n")
        ser.flush()  # Ensure command is sent immediately
        
        # Step 4: Hold active state longer (cleanup)
        time.sleep(0.100)  # 100ms hold (pins stay active longer)
        
        # Step 5: Reset both pins to idle state
        ser.write(b"PIN5_HIGH\n")  # Pin 5 back to HIGH (5V)
        ser.write(b"PIN6_LOW\n")   # Pin 6 back to LOW (0V)
        ser.flush()  # Ensure commands are sent
        
    except Exception as e:
        print(f"Error in arcade_button_press: {e}")
        # Try to reset GPIO on error
        try:
            ser.write(b"RESET_GPIO\n")
            ser.flush()
        except:
            pass


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
    global armed, peak, cap_end, pulse_count
    
    print("GPIO control now handled by Arduino - no Pi GPIO needed!")
    print("Arduino will control arcade motherboard pins via Serial commands.")
    
    print("Initializing serial connection...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
        time.sleep(0.2)
        ser.reset_input_buffer()
    except Exception as e:
        print(f"ERROR: Could not open serial port {SERIAL_PORT}: {e}", file=sys.stderr)
        serial_running = False
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
        # GPIO PULSE GENERATION LOGIC (Arduino GPIO control)
        # ============================================================
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
                # Map amplitude to pulse width INVERSELY
                # High peak → Short pulse (strong hit = quick button press)
                # Low peak → Long pulse (weak hit = slow button press)
                a_clamped = clamp(peak, A_MIN, A_MAX)
                width_ms = clamp(
                    map_linear_inverse(a_clamped, A_MIN, A_MAX, W_MIN_MS, W_MAX_MS),
                    W_MIN_MS, W_MAX_MS
                )
                
                pulse_count += 1
                print(f"Pulse #{pulse_count}: Peak={peak:.1f} → {width_ms:.0f} ms (INVERTED)")
                
                # Generate arcade button press using Arduino GPIO control
                arcade_button_press(ser, width_ms)
                
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
    # Send reset command to Arduino to reset GPIO pins
    try:
        if ser and not ser.closed:
            ser.write(b"RESET_GPIO\n")
            ser.flush()
    except:
        pass
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
    print("SICK PBT Sensor - Arduino GPIO Control + Web Visualization")
    print("=" * 60)
    print(f"Serial port: {SERIAL_PORT} @ {BAUD} baud")
    print(f"Samples per second: {SAMPLES_PER_SEC}")
    print(f"Arcade Interface (Arduino GPIO):")
    print(f"  Arduino Pin 6: Press START signal (Active HIGH, 5V output)")
    print(f"  Arduino Pin 5: Press ACTIVE signal (Active LOW, 0V output)")
    print(f"Pulse Mapping: HIGH peak → SHORT pulse (INVERTED)")
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
        # Send reset command to Arduino to reset GPIO pins
        try:
            if ser and not ser.closed:
                ser.write(b"RESET_GPIO\n")
                ser.flush()
        except:
            pass

