#!/usr/bin/env python3
"""
PBT Scoring System Tester with Real Waveform Simulation
Test the scoring system with realistic PBT waveforms and send real signals to arcade
"""
import time
import serial
import threading
from collections import deque
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# Improved proportional scoring logic
A_MIN, A_MAX = 30, 100  # Wider range: 30-100 ADC
W_MIN_MS, W_MAX_MS = 10, 100  # Pulse width: 10-100ms
TRIGGER_THRESHOLD = 30  # Higher threshold for better sensitivity

# Serial connection for Arduino
SERIAL_PORT = "/dev/ttyUSB0"
BAUD = 115200
ser = None

# Waveform data for real-time display
waveform_data = deque(maxlen=4000)  # 5 seconds at 800Hz
envelope_data = deque(maxlen=4000)
time_data = deque(maxlen=4000)
baseline = 512.0
envelope = 0.0
sample_count = 0
armed = True
peak = 0.0
cap_end = 0.0
pulse_count = 0

# Threading
data_lock = threading.Lock()
serial_running = False

def clamp(x, lo, hi):
    """Clamp value between min and max."""
    return max(lo, min(hi, x))

def map_linear_inverse(x, x0, x1, y0, y1):
    """Map value from one range to another INVERSELY (high x → low y)."""
    if x1 <= x0:
        return y1
    t = (x - x0) / (x1 - x0)
    return y1 - t * (y1 - y0)  # Inverted: subtract instead of add

def calculate_pulse_width(peak):
    """Calculate pulse width from peak value - map 30-100 ADC to 40-10ms."""
    a_clamped = clamp(peak, A_MIN, A_MAX)
    
    # Map 30-100 ADC to 40-10ms pulse width for better distribution
    # 30 ADC -> 40ms (good score)
    # 100 ADC -> 10ms (maximum score)
    # Linear mapping across the full range
    
    width_ms = 40 - (a_clamped - 30) * (30 / 70)  # 30->40ms, 100->10ms
    
    return clamp(width_ms, W_MIN_MS, W_MAX_MS)

def get_score_level(pulse_width):
    """Determine score level based on pulse width."""
    if pulse_width < 20:
        return "HIGH SCORE (Short pulse)"
    elif pulse_width < 50:
        return "MEDIUM SCORE"
    else:
        return "LOW SCORE (Long pulse)"

def calculate_arcade_score_from_pulse_width(pulse_width_ms):
    """Calculate arcade score based on actual pulse width duration."""
    # Based on your observations with better distribution:
    # 100ms -> 140 score
    # 80ms  -> 200 score  
    # 60ms  -> 280 score
    # 40ms  -> 380 score
    # 20ms  -> 450 score
    # 10ms  -> 500 score
    
    if pulse_width_ms >= 100:
        return 140
    elif pulse_width_ms >= 80:
        # Linear interpolation: 100ms->140, 80ms->200
        return int(140 + (100 - pulse_width_ms) * (60 / 20))
    elif pulse_width_ms >= 60:
        # Linear interpolation: 80ms->200, 60ms->280
        return int(200 + (80 - pulse_width_ms) * (80 / 20))
    elif pulse_width_ms >= 40:
        # Linear interpolation: 60ms->280, 40ms->380
        return int(280 + (60 - pulse_width_ms) * (100 / 20))
    elif pulse_width_ms >= 20:
        # Linear interpolation: 40ms->380, 20ms->450
        return int(380 + (40 - pulse_width_ms) * (70 / 20))
    elif pulse_width_ms >= 10:
        # Linear interpolation: 20ms->450, 10ms->500
        return int(450 + (20 - pulse_width_ms) * (50 / 10))
    else:
        return 500  # Very short pulses get max score

def calculate_arcade_score(peak):
    """Calculate arcade score from peak value."""
    pulse_width = calculate_pulse_width(peak)
    return calculate_arcade_score_from_pulse_width(pulse_width)

def arcade_button_press(ser, duration_ms):
    """Send arcade button press to Arduino."""
    try:
        # Pin 6 HIGH (press start)
        ser.write(b"PIN6_HIGH\n")
        ser.flush()
        
        # Wait for duration
        time.sleep(duration_ms / 1000.0)
        
        # Pin 5 LOW (press confirmed)
        ser.write(b"PIN5_LOW\n")
        ser.flush()
        
        # Hold active state
        time.sleep(0.100)
        
        # Reset pins
        ser.write(b"PIN5_HIGH\n")
        ser.write(b"PIN6_LOW\n")
        ser.flush()
        
        return True
    except Exception as e:
        print(f"Error sending arcade signal: {e}")
        return False

def init_arduino():
    """Initialize Arduino connection."""
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
        time.sleep(0.2)
        ser.reset_input_buffer()
        print(f"Arduino connected on {SERIAL_PORT}")
        return True
    except Exception as e:
        print(f"Arduino connection failed: {e}")
        return False

def read_one_int(ser):
    """Read one line and parse int; return None on empty/invalid."""
    try:
        s = ser.readline().decode(errors="ignore").strip()
        if not s:
            return None
        
        # Skip non-numeric data (system messages)
        if not s.isdigit():
            return None
            
        return int(s)
    except (ValueError, UnicodeDecodeError):
        return None

def process_waveform_data(value):
    """Process waveform data through the same algorithm as real PBT."""
    global baseline, envelope, sample_count, armed, peak, cap_end, pulse_count
    
    sample_count += 1
    current_time = time.time()
    
    # Update baseline and envelope (same as app_combined.py)
    baseline = (1 - 0.001) * baseline + 0.001 * value  # BASELINE_ALPHA = 0.001
    xmag = abs(value - baseline)
    envelope = (1 - 0.12) * envelope + 0.12 * xmag     # ENVELOPE_ALPHA = 0.12
    
    # Peak detection logic (same as app_combined.py)
    if armed:
        # Check for trigger
        if envelope > TRIGGER_THRESHOLD:
            armed = False
            peak = envelope
            cap_end = current_time + (250 / 1000.0)  # CAPTURE_MS = 250
            print(f"Peak detected: {envelope:.1f} ADC")
    else:
        # Capture peak during capture window
        if envelope > peak:
            peak = envelope
        
        # Check if capture window ended or envelope dropped
        if current_time >= cap_end or envelope < (TRIGGER_THRESHOLD * 0.5):
            # Use updated pulse width calculation
            width_ms = calculate_pulse_width(peak)
            arcade_score = calculate_arcade_score_from_pulse_width(width_ms)
            
            pulse_count += 1
            print(f"Pulse #{pulse_count}: Peak={peak:.1f} → {width_ms:.1f}ms → {arcade_score}pts")
            
            # Send arcade signal if Arduino connected
            if ser and not ser.closed:
                arcade_button_press(ser, width_ms)
                print(f"  Arcade signal sent: {width_ms:.1f}ms pulse")
            
            # Wait to re-arm until envelope falls below rearm level
            while envelope >= (TRIGGER_THRESHOLD * 0.4):  # REARM_LEVEL
                time.sleep(0.001)
                # In real system, we'd read more data here
                break  # Simplified for testing
            
            armed = True

def serial_reader_thread():
    """Background thread to read waveform data from Arduino."""
    global ser, serial_running, sample_count
    
    print("Starting waveform reader thread...")
    
    while serial_running:
        if ser and not ser.closed:
            value = read_one_int(ser)
            if value is not None:
                # Process the waveform data
                process_waveform_data(value)
                
                # Store for web display
                with data_lock:
                    waveform_data.append(value)
                    envelope_data.append(envelope)
                    time_data.append(time.time())
        else:
            time.sleep(0.01)
    
    print("Waveform reader thread stopped")

def start_serial_thread():
    """Start the serial reader thread."""
    global serial_running
    serial_running = True
    thread = threading.Thread(target=serial_reader_thread, daemon=True)
    thread.start()
    return thread

# Web interface for testing
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pbt-tester-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@app.route('/')
def index():
    """PBT testing interface."""
    return render_template('pbt_tester.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('PBT Tester: Client connected')
    
    # Send initial configuration
    emit('config', {
        'trigger_threshold': TRIGGER_THRESHOLD,
        'peak_range': f"{A_MIN}-{A_MAX}",
        'pulse_range': f"{W_MIN_MS}-{W_MAX_MS}ms",
        'mapping': "30-100 ADC → 40-10ms (Optimized Distribution)",
        'simulation_mode': True,
        'waveform_enabled': True
    })
    
    # Send current waveform data
    with data_lock:
        if waveform_data:
            emit('waveform_data', {
                'waveform': list(waveform_data),
                'envelope': list(envelope_data),
                'time': list(time_data),
                'baseline': baseline,
                'envelope_val': envelope,
                'armed': armed,
                'peak': peak
            })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('PBT Tester: Client disconnected')

@socketio.on('test_peak')
def handle_test_peak(data):
    """Test a single peak value."""
    try:
        peak = float(data['peak'])
        
        # Calculate pulse width and arcade score
        pulse_width = calculate_pulse_width(peak)
        arcade_score = calculate_arcade_score(peak) if peak >= TRIGGER_THRESHOLD else 0
        
        # Determine if it would trigger
        triggered = peak >= TRIGGER_THRESHOLD
        
        # Get score level
        score_level = get_score_level(pulse_width) if triggered else "NO SCORE (Below threshold)"
        
        # Send results back
        emit('peak_result', {
            'peak': peak,
            'pulse_width': pulse_width,
            'arcade_score': arcade_score,
            'triggered': triggered,
            'threshold': TRIGGER_THRESHOLD,
            'score_level': score_level,
            'range': f"{A_MIN}-{A_MAX} → 40-10ms (Optimized)"
        })
        
        print(f"Test Peak: {peak:.1f} → Pulse: {pulse_width:.0f}ms {'(TRIGGERED)' if triggered else '(Below threshold)'}")
        
    except (ValueError, KeyError) as e:
        emit('error', {'message': f'Invalid peak value: {e}'})

@socketio.on('test_range')
def handle_test_range(data):
    """Test a range of peak values."""
    try:
        start = float(data.get('start', A_MIN))
        end = float(data.get('end', A_MAX))
        step = float(data.get('step', 2.0))
        
        results = []
        current = start
        while current <= end:
            pulse_width = calculate_pulse_width(current)
            arcade_score = calculate_arcade_score(current) if current >= TRIGGER_THRESHOLD else 0
            triggered = current >= TRIGGER_THRESHOLD
            score_level = get_score_level(pulse_width) if triggered else "NO SCORE"
            
            results.append({
                'peak': current,
                'pulse_width': pulse_width,
                'arcade_score': arcade_score,
                'triggered': triggered,
                'score_level': score_level
            })
            current += step
        
        emit('range_result', {
            'results': results,
            'start': start,
            'end': end,
            'step': step
        })
        
        print(f"Range test: {start}-{end} (step {step}) - {len(results)} values tested")
        
    except (ValueError, KeyError) as e:
        emit('error', {'message': f'Invalid range parameters: {e}'})

@socketio.on('test_specific')
def handle_test_specific(data):
    """Test specific peak values."""
    try:
        values = data.get('values', [30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100])
        
        results = []
        for peak in values:
            pulse_width = calculate_pulse_width(peak)
            arcade_score = calculate_arcade_score(peak) if peak >= TRIGGER_THRESHOLD else 0
            triggered = peak >= TRIGGER_THRESHOLD
            score_level = get_score_level(pulse_width) if triggered else "NO SCORE"
            
            results.append({
                'peak': peak,
                'pulse_width': pulse_width,
                'arcade_score': arcade_score,
                'triggered': triggered,
                'score_level': score_level
            })
        
        emit('specific_result', {
            'results': results,
            'values': values
        })
        
        print(f"Specific test: {len(values)} values tested")
        
    except (ValueError, KeyError) as e:
        emit('error', {'message': f'Invalid specific values: {e}'})

@socketio.on('simulate_hit')
def handle_simulate_hit(data):
    """Simulate a complete PBT hit sequence with real arcade signals."""
    try:
        peak = float(data['peak'])
        
        if peak < TRIGGER_THRESHOLD:
            emit('simulation_result', {
                'success': False,
                'message': f'Peak {peak:.1f} below threshold {TRIGGER_THRESHOLD} - No hit detected'
            })
            return
        
        # Calculate pulse width and arcade score
        pulse_width = calculate_pulse_width(peak)
        score_level = get_score_level(pulse_width)
        arcade_score = calculate_arcade_score(peak)
        
        # Send real arcade signal if Arduino connected
        arcade_success = False
        if ser and not ser.closed:
            arcade_success = arcade_button_press(ser, pulse_width)
        
        # Simulate the complete sequence
        emit('simulation_result', {
            'success': True,
            'peak': peak,
            'pulse_width': pulse_width,
            'score_level': score_level,
            'arcade_score': arcade_score,
            'arcade_signal': arcade_success,
            'sequence': [
                f"1. Peak detected: {peak:.1f} ADC counts",
                f"2. Above threshold: {TRIGGER_THRESHOLD} ✓",
                f"3. Pulse width calculated: {pulse_width:.1f}ms",
                f"4. Arcade score: {arcade_score} points",
                f"5. Arcade signal sent: {'SUCCESS' if arcade_success else 'FAILED'}",
                f"6. Score level: {score_level}",
                f"7. Arduino status: {'Connected' if ser and not ser.closed else 'Disconnected'}"
            ]
        })
        
        print(f"Hit: Peak {peak:.1f} → {pulse_width:.1f}ms pulse → {score_level} → Arcade: {'OK' if arcade_success else 'FAIL'}")
        
    except (ValueError, KeyError) as e:
        emit('error', {'message': f'Invalid simulation parameters: {e}'})

@socketio.on('send_arcade_signal')
def handle_send_arcade_signal(data):
    """Send arcade signal directly."""
    try:
        pulse_width = float(data['pulse_width'])
        
        if ser and not ser.closed:
            success = arcade_button_press(ser, pulse_width)
            emit('arcade_signal_result', {
                'success': success,
                'pulse_width': pulse_width,
                'message': f'Arcade signal sent: {pulse_width:.1f}ms - {"SUCCESS" if success else "FAILED"}'
            })
            print(f"Direct arcade signal: {pulse_width:.1f}ms - {'SUCCESS' if success else 'FAILED'}")
        else:
            emit('arcade_signal_result', {
                'success': False,
                'pulse_width': pulse_width,
                'message': 'Arduino not connected'
            })
        
    except (ValueError, KeyError) as e:
        emit('error', {'message': f'Invalid pulse width: {e}'})

@socketio.on('get_waveform_data')
def handle_get_waveform_data():
    """Send current waveform data to client."""
    with data_lock:
        emit('waveform_data', {
            'waveform': list(waveform_data),
            'envelope': list(envelope_data),
            'time': list(time_data),
            'baseline': baseline,
            'envelope_val': envelope,
            'armed': armed,
            'peak': peak,
            'sample_count': sample_count,
            'pulse_count': pulse_count
        })


@socketio.on('generate_custom_peak')
def handle_generate_custom_peak(data):
    """Generate a custom peak with specified amplitude."""
    try:
        amplitude = int(data['amplitude'])
        if ser and not ser.closed:
            command = f"CUSTOM_PEAK:{amplitude}\n"
            ser.write(command.encode())
            ser.flush()
            print(f"Generated custom peak: {amplitude} ADC")
            emit('custom_peak_result', {
                'success': True,
                'amplitude': amplitude,
                'message': f'Custom peak generated: {amplitude} ADC'
            })
        else:
            emit('custom_peak_result', {
                'success': False,
                'amplitude': amplitude,
                'message': 'Arduino not connected'
            })
    except (ValueError, KeyError) as e:
        emit('error', {'message': f'Invalid amplitude: {e}'})

@socketio.on('start_simulation')
def handle_start_simulation():
    """Start the Arduino simulation."""
    if ser and not ser.closed:
        ser.write(b"START_SIMULATION\n")
        ser.flush()
        print("Started Arduino simulation")

@socketio.on('stop_simulation')
def handle_stop_simulation():
    """Stop the Arduino simulation."""
    if ser and not ser.closed:
        ser.write(b"STOP_SIMULATION\n")
        ser.flush()
        print("Stopped Arduino simulation")

if __name__ == '__main__':
    print("=" * 60)
    print("SICK7 PBT Tester - Real Waveform Simulation")
    print("=" * 60)
    print(f"Trigger: {TRIGGER_THRESHOLD} ADC")
    print(f"Peak Range: {A_MIN}-{A_MAX} ADC")
    print(f"Pulse Range: {W_MIN_MS}-{W_MAX_MS} ms")
    print(f"Web: http://localhost:5002")
    print(f"Oscilloscope: Pin 3 (PWM), Pin 6 (Arcade), Pin 5 (Arcade)")
    print("=" * 60)
    
    # Try to connect to Arduino
    arduino_connected = init_arduino()
    if not arduino_connected:
        print("WARNING: Arduino not connected - testing without arcade signals")
    else:
        # Start the serial reader thread
        start_serial_thread()
        print("Waveform reader thread started")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5002, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\nStopping PBT Tester...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        serial_running = False
        if ser and not ser.closed:
            ser.close()
