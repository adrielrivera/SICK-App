#!/usr/bin/env python3
"""
SICK Capstone - PBT Sensor Web App
Real-time waveform visualization
"""
import time
import sys
from threading import Thread, Lock
from collections import deque
import serial
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

# Statistics
baseline = 0.0
envelope = 0.0
sample_count = 0


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
    """Background thread to read serial data and update buffers."""
    global ser, serial_running, baseline, envelope, sample_count
    
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
        
        # Emit data in batches
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
                'threshold': TRIGGER_THRESHOLD
            })
            
            batch_raw = []
            batch_env = []
            batch_time = []
            last_emit = now
    
    if ser:
        ser.close()
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
            'threshold': TRIGGER_THRESHOLD
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
        'buffer_size': len(raw_buffer)
    })


def start_serial_thread():
    """Start the serial reader thread."""
    global serial_running
    serial_running = True
    thread = Thread(target=serial_reader_thread, daemon=True)
    thread.start()
    return thread


if __name__ == '__main__':
    print("Starting SICK PBT Sensor Web App...")
    print(f"Serial port: {SERIAL_PORT} @ {BAUD} baud")
    print(f"Samples per second: {SAMPLES_PER_SEC}")
    print(f"Server: http://{HOST}:{PORT}")
    
    # Start serial reader thread
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

