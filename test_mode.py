#!/usr/bin/env python3
"""
SICK PBT Sensor Web App - Test Mode
Simulates sensor data without requiring Arduino connection
"""
import time
import sys
import math
import random
from threading import Thread, Lock
from collections import deque
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

# Simulation state
sim_running = False
baseline = 40.0
envelope = 0.0
sample_count = 0


class SignalSimulator:
    """Simulates PBT sensor signal similar to Arduino simulator"""
    
    def __init__(self):
        self.baseline = 40
        self.noise_amp = 6
        self.peak = 500
        self.in_hit = False
        self.phase = 0.0
        self.phase_step = 0.0
        self.last_hit_time = time.time()
        self.hit_gap = 3.0
    
    def start_new_hit(self):
        """Start a new simulated hit"""
        self.peak = random.randint(200, 900)
        hit_duration_ms = random.randint(120, 320)
        self.phase = 0.0
        self.phase_step = math.pi / (hit_duration_ms * (SAMPLES_PER_SEC / 1000.0))
        self.in_hit = True
    
    def get_next_sample(self):
        """Generate next sample value"""
        now = time.time()
        
        # Randomly start a hit
        if not self.in_hit and (now - self.last_hit_time) > self.hit_gap:
            self.start_new_hit()
            self.last_hit_time = now
            self.hit_gap = 2.5 + random.uniform(-0.8, 0.8)
        
        # Base value with noise
        value = self.baseline + random.randint(-self.noise_amp, self.noise_amp + 1)
        
        # Add hit envelope
        if self.in_hit:
            env = math.sin(self.phase)
            hit_add = int(env * (self.peak - self.baseline))
            value = self.baseline + hit_add
            self.phase += self.phase_step
            
            if self.phase >= math.pi:
                self.in_hit = False
        
        # Clamp to ADC range
        return max(0, min(1023, value))


def simulator_thread():
    """Background thread to simulate sensor data"""
    global sim_running, baseline, envelope, sample_count
    
    print("Starting signal simulator...")
    simulator = SignalSimulator()
    
    # Baseline warm-up
    baseline_samples = [simulator.get_next_sample() for _ in range(160)]
    baseline = sum(baseline_samples) / len(baseline_samples)
    envelope = 0.0
    
    print(f"Simulated baseline: {baseline:.1f} ADC counts")
    
    # Main simulation loop
    start_time = time.time()
    sample_count = 0
    last_emit = time.time()
    
    batch_raw = []
    batch_env = []
    batch_time = []
    
    sample_interval = 1.0 / SAMPLES_PER_SEC
    next_sample_time = time.time()
    
    while sim_running:
        now = time.time()
        
        if now >= next_sample_time:
            # Generate sample
            v = simulator.get_next_sample()
            sample_count += 1
            current_time = now - start_time
            
            # Update baseline and envelope
            baseline = (1 - BASELINE_ALPHA) * baseline + BASELINE_ALPHA * v
            xmag = abs(v - baseline)
            envelope = (1 - ENVELOPE_ALPHA) * envelope + ENVELOPE_ALPHA * xmag
            
            # Store in batch
            batch_raw.append(v)
            batch_env.append(envelope)
            batch_time.append(current_time)
            
            next_sample_time += sample_interval
        
        # Emit data in batches
        if now - last_emit >= EMIT_INTERVAL:
            if batch_raw:
                with data_lock:
                    raw_buffer.extend(batch_raw)
                    env_buffer.extend(batch_env)
                    time_buffer.extend(batch_time)
                
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
        
        # Small sleep to prevent CPU spinning
        time.sleep(0.001)
    
    print("Signal simulator stopped")


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    
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
    """Handle client disconnection"""
    print('Client disconnected')


@socketio.on('request_stats')
def handle_stats_request():
    """Send current statistics"""
    emit('stats', {
        'sample_count': sample_count,
        'baseline': baseline,
        'envelope': envelope,
        'buffer_size': len(raw_buffer)
    })


def start_simulator_thread():
    """Start the simulator thread"""
    global sim_running
    sim_running = True
    thread = Thread(target=simulator_thread, daemon=True)
    thread.start()
    return thread


if __name__ == '__main__':
    print("=" * 50)
    print("  SICK PBT Sensor Web App - TEST MODE")
    print("  (Simulated data - no Arduino required)")
    print("=" * 50)
    print(f"Simulated sample rate: {SAMPLES_PER_SEC} Hz")
    print(f"Server: http://{HOST}:{PORT}")
    print("")
    
    # Start simulator thread
    start_simulator_thread()
    
    try:
        # Run Flask app
        socketio.run(app, host=HOST, port=PORT, debug=DEBUG)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        sim_running = False

