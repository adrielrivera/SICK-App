#!/usr/bin/env python3
"""
SICK7 - Combined PBT Sensor Web App with GPIO Pulse Output + Credit Tracking
Real-time waveform visualization + GPIO pulse generation + Credit system
Credit system: 2 PBT hits = 1 credit deducted
LiDAR safety disabled when credits == 0
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
A_MIN, A_MAX = 30, 100  # Improved proportional range (30-100) for better scoring
W_MIN_MS, W_MAX_MS = 10, 100  # Shorter max pulse for better high scores
REARM_LEVEL = TRIGGER_THRESHOLD * 0.4

# Grounding issue filtering
MIN_VALID_READING = 10  # Reject readings below this (grounding issues cause near-0 readings)
MIN_PEAK_THRESHOLD = 25  # Minimum peak to accept (higher than TRIGGER_THRESHOLD to filter noise)

# Statistics for pulse generation
pulse_count = 0

# Safety system
game_enabled = True

# LiDAR alarm Arduino (OR gate) serial config
LIDAR_SERIAL_PORT = "/dev/ttyUSB1"  # Second Arduino
LIDAR_BAUD = 9600                    # Matches lidar_detection.ino
lidar_ser = None
lidar_thread = None

# LiDAR status (simplified OR-gated system)
lidar_person_detected = False
lidar_alarm_active = False

# Credit tracking system (shared between threads)
credits_lock = Lock()
credits = 0  # Current credit count (tracked from Arduino)


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


def calculate_pulse_width(peak):
    """Calculate pulse width from peak value - map 30-100 ADC to 40-10ms (same as pbt_tester.py)."""
    a_clamped = clamp(peak, A_MIN, A_MAX)
    
    # Map 30-100 ADC to 40-10ms pulse width for better distribution
    # 30 ADC -> 40ms (good score)
    # 100 ADC -> 10ms (maximum score)
    # Linear mapping across the full range (same as pbt_tester.py)
    width_ms = 40 - (a_clamped - 30) * (30 / 70)  # 30->40ms, 100->10ms
    
    return clamp(width_ms, W_MIN_MS, W_MAX_MS)


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
        
        # Skip non-numeric data (system messages)
        if not s.isdigit():
            return None
            
        return int(s)
    except (ValueError, UnicodeDecodeError):
        return None


def read_arduino_messages(ser):
    """Read and display Arduino status messages, including credit updates."""
    global tim100_detected, tim150_detected, credits
    try:
        # Limit the number of lines read per call to prevent blocking
        lines_read = 0
        max_lines_per_call = 10
        
        while ser.in_waiting > 0 and lines_read < max_lines_per_call:
            line = ser.readline().decode(errors="ignore").strip()
            lines_read += 1
            
            # Skip raw PBT data (just numbers) - only process system messages
            if line and line.isdigit():
                continue  # Skip raw PBT sensor data
            
            # Parse credit status updates
            if line.startswith("CREDITS:"):
                try:
                    new_credits = int(line.split(":")[1].strip())
                    with credits_lock:
                        old_credits = credits
                        credits = max(0, new_credits)  # Ensure non-negative
                    if old_credits != credits:
                        print(f"💰 Credits updated: {credits} (was {old_credits})")
                        # Emit credit update to web clients
                        socketio.emit('credit_status', {
                            'credits': credits,
                            'changed': True
                        })
                except (ValueError, IndexError) as e:
                    print(f"Error parsing CREDITS: {e}")
            
            # Debug: Print only system messages
            if line and (line.startswith("#") or "TiM" in line or "CREDIT" in line or "PBT_HIT" in line):
                print(f"DEBUG PBT Arduino: '{line}'")
            
            if line and line.startswith("#"):
                print(f"  Arduino: {line}")
                # No per-sensor parsing needed here
            elif "TiM100 DETECTED" in line:
                tim100_detected = True
                print(f"  Arduino: TiM100 DETECTED - Person on LEFT side")
            elif "TiM100 CLEAR" in line:
                tim100_detected = False
                print(f"  Arduino: TiM100 CLEAR - LEFT side clear")
            elif "TiM150 DETECTED" in line:
                tim150_detected = True
                print(f"  Arduino: TiM150 DETECTED - Person on RIGHT side")
            elif "TiM150 CLEAR" in line:
                tim150_detected = False
                print(f"  Arduino: TiM150 CLEAR - RIGHT side clear")
    except Exception as e:
        print(f"DEBUG PBT Serial Error: {e}")
        pass  # Ignore serial read errors

def get_combined_lidar_status():
    """Get combined status from all LiDARs. CRITICAL: Ignore LiDAR when credits == 0."""
    global lidar_person_detected, lidar_alarm_active, credits
    
    # CREDIT OVERRIDE: When credits == 0, always return SAFE (ignore LiDAR)
    with credits_lock:
        current_credits = credits
    
    if current_credits == 0:
        # No credits = LiDAR safety disabled (allows testing/play without credits)
        return "SAFE", {
            'rear': False,
            'left': False,
            'right': False,
            'areas': [],
            'credits_zero_override': True  # Flag to indicate override
        }
    
    # Normal LiDAR safety logic when credits > 0
    if lidar_person_detected:
        return "DANGER", {
            'rear': False,
            'left': False,
            'right': False,
            'areas': ["ANY"]
        }
    else:
        return "SAFE", {
            'rear': False,
            'left': False,
            'right': False,
            'areas': []
        }


def lidar_reader_thread():
    """Background thread: read LiDAR alarm Arduino on ttyUSB1 and update person_detected."""
    global lidar_ser, lidar_person_detected, lidar_alarm_active
    try:
        lidar_ser = serial.Serial(LIDAR_SERIAL_PORT, LIDAR_BAUD, timeout=1)
        time.sleep(0.2)
        lidar_ser.reset_input_buffer()
        print(f"DEBUG LIDAR: Arduino connected on {LIDAR_SERIAL_PORT} @ {LIDAR_BAUD} baud")
    except Exception as e:
        print(f"WARNING: Could not open LiDAR serial {LIDAR_SERIAL_PORT}: {e}")
        return

    last_emit = 0
    while serial_running:
        try:
            while lidar_ser.in_waiting > 0:
                line = lidar_ser.readline().decode(errors='ignore').strip()
                if not line:
                    continue
                if line.startswith("LIDAR_STATUS:"):
                    # Format: LIDAR_STATUS:person,alarm  where 1/0
                    try:
                        status = line.split(":",1)[1]
                        parts = status.split(",")
                        if len(parts) >= 2:
                            new_person_detected = (parts[0].strip() == "1")
                            lidar_alarm_active = (parts[1].strip() == "1")
                            
                            # Check for state change and immediately emit
                            if new_person_detected != lidar_person_detected:
                                lidar_person_detected = new_person_detected
                                status_str, info = get_combined_lidar_status()
                                socketio.emit('safety_status', {
                                    'status': status_str,
                                    'game_enabled': (status_str == 'SAFE'),
                                    'areas': info
                                })
                                print(f"🔄 LiDAR state changed: {'DANGER' if lidar_person_detected else 'SAFE'}")
                            else:
                                lidar_person_detected = new_person_detected
                    except Exception as e:
                        print(f"Error parsing LIDAR_STATUS: {e}")
                        pass
                elif line.startswith("PERSON_DETECTED"):
                    if not lidar_person_detected:
                        lidar_person_detected = True
                        status_str, info = get_combined_lidar_status()
                        socketio.emit('safety_status', {
                            'status': status_str,
                            'game_enabled': (status_str == 'SAFE'),
                            'areas': info
                        })
                elif "Area clear" in line or "✅" in line:
                    # Clear message from Arduino - force immediate update
                    if lidar_person_detected:
                        lidar_person_detected = False
                        status_str, info = get_combined_lidar_status()
                        socketio.emit('safety_status', {
                            'status': status_str,
                            'game_enabled': (status_str == 'SAFE'),
                            'areas': info
                        })
                        print(f"🔄 LiDAR cleared: SAFE")
                elif line.startswith("#"):
                    print(f"  LiDAR Arduino: {line}")

            # Periodically emit safety status to clients (backup, state changes emit immediately)
            now = time.time()
            if now - last_emit > 0.5:
                status_str, info = get_combined_lidar_status()
                socketio.emit('safety_status', {
                    'status': status_str,
                    'game_enabled': (status_str == 'SAFE'),
                    'areas': info
                })
                last_emit = now
        except Exception as e:
            # Keep thread alive on transient serial errors
            time.sleep(0.1)
            continue


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
        print(f"DEBUG PBT: Arduino connected on {SERIAL_PORT} @ {BAUD} baud")
        
        # Test connection by reading a few lines
        print("DEBUG PBT: Testing Arduino connection...")
        for i in range(3):
            if ser.in_waiting > 0:
                line = ser.readline().decode(errors="ignore").strip()
                if line:
                    print(f"DEBUG PBT Test read: '{line}'")
            time.sleep(0.5)
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
    
    # Initialize envelope from initial readings to avoid high startup spike
    envelope_samples = []
    t1 = time.time()
    while time.time() - t1 < 0.1:  # 100ms of envelope samples
        v = read_one_int(ser)
        if v is not None and v >= MIN_VALID_READING:  # Filter grounding issues
            xmag = abs(v - baseline)
            envelope_samples.append(xmag)
    
    if envelope_samples:
        envelope = sum(envelope_samples) / len(envelope_samples)  # Start with average
    else:
        envelope = 0.0  # Fallback
    
    print(f"Baseline calibrated: {baseline:.1f} ADC counts")
    print(f"Envelope initialized: {envelope:.1f} ADC counts")
    
    # Main reading loop
    start_time = time.time()
    sample_count = 0
    last_emit = time.time()
    last_status_request = time.time()
    emit_interval = EMIT_INTERVAL  # Emit data at configured rate
    
    batch_raw = []
    batch_env = []
    batch_time = []
    
    while serial_running:
        # ============================================================
        # GET CURRENT TIME FIRST
        # ============================================================
        now = time.time()
        
        # ============================================================
        # READ ARDUINO MESSAGES MULTIPLE TIMES (Credit tracking, status updates)
        # ============================================================
        for _ in range(3):  # Read Arduino messages multiple times per loop
            read_arduino_messages(ser)
            time.sleep(0.001)  # Small delay between reads
        
        # Periodic status request every 2 seconds
        if now - last_status_request > 2.0:
            try:
                ser.write(b"STATUS\n")
                ser.flush()
                last_status_request = now
            except Exception as e:
                print(f"Error sending periodic STATUS: {e}")
        
        # ============================================================
        # READ RAW PBT DATA (Non-blocking for PBT system)
        # ============================================================
        v = None
        if ser.in_waiting > 0:
            v = read_one_int(ser)
        
        if v is None:
            time.sleep(0.001)
            continue
        
        # Filter out grounding issues: reject readings that are too low (sudden drop to 0)
        if v < MIN_VALID_READING:
            # Skip this reading - likely a grounding issue causing false spike in envelope
            continue
        
        sample_count += 1
        current_time = time.time() - start_time
        
        # Periodic serial buffer reset to prevent overflow
        if sample_count % 1000 == 0:
            ser.reset_input_buffer()
            print("DEBUG: Reset serial input buffer")
        
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
        
        # Check combined LiDAR status
        safety_status, safety_info = get_combined_lidar_status()
        game_enabled = (safety_status == "SAFE")
        
        # Check credits before pulse generation
        with credits_lock:
            current_credits = credits
        
        # Only process pulse generation if game is enabled AND credits > 0
        # When disabled or no credits, keep system armed but continue reading serial data normally
        if game_enabled and current_credits > 0:
            if armed:
                # Check for trigger (only when armed)
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
                    # Validate peak before processing - reject if too low (likely grounding issue)
                    if peak < MIN_PEAK_THRESHOLD:
                        print(f"⚠️  Rejected false hit: Peak={peak:.1f} below minimum threshold {MIN_PEAK_THRESHOLD}")
                        armed = True  # Re-arm immediately
                        continue
                    
                    # Map amplitude to pulse width (same calculation as pbt_tester.py)
                    # High peak → Short pulse (strong hit = quick button press)
                    # Low peak → Long pulse (weak hit = slow button press)
                    width_ms = calculate_pulse_width(peak)
                    
                    pulse_count += 1
                    print(f"Pulse #{pulse_count}: Peak={peak:.1f} → {width_ms:.0f} ms (INVERTED)")
                    print(f"  Mapping: Peak {peak:.1f} → Pulse {width_ms:.0f}ms (Range: {A_MIN}-{A_MAX} → {W_MIN_MS}-{W_MAX_MS}ms)")
                    
                    # Send PBT hit notification to Arduino for credit tracking
                    try:
                        ser.write(b"PBT_HIT\n")
                        ser.flush()
                        print("  PBT_HIT sent to Arduino for credit tracking")
                        
                        # IMMEDIATELY read Arduino response messages multiple times
                        for i in range(10):  # Read multiple times to catch all responses
                            read_arduino_messages(ser)
                            time.sleep(0.01)  # Small delay between reads
                            
                    except Exception as e:
                        print(f"  Error sending PBT_HIT: {e}")
                    
                    # Request credit status from Arduino
                    try:
                        ser.write(b"STATUS\n")
                        ser.flush()
                        
                        # Read Arduino response to STATUS command
                        for i in range(5):
                            read_arduino_messages(ser)
                            time.sleep(0.01)
                            
                    except Exception as e:
                        print(f"  Error requesting status: {e}")
                    
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
                    
                    # Re-arm as soon as envelope falls below REARM_LEVEL
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
        else:
            # Game disabled - keep system armed, suppress all pulse generation
            # Continue reading serial data normally (don't skip the loop)
            armed = True
        
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
    return render_template('index_with_credits.html')


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
    
    # Send initial safety status
    emit('safety_status', {
        'status': 'safe' if game_enabled else 'danger',
        'game_enabled': game_enabled
    })
    
    # Send initial credit status
    with credits_lock:
        emit('credit_status', {
            'credits': credits,
            'changed': False
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


@socketio.on('request_safety_status')
def handle_safety_request():
    """Send current safety status to client."""
    emit('safety_status', {
        'status': 'safe' if game_enabled else 'danger',
        'game_enabled': game_enabled
    })


@socketio.on('test_person_detected')
def handle_test_person():
    """Test function to simulate person detection."""
    global tim240_alert
    tim240_alert = True
    safety_status, safety_info = get_combined_lidar_status()
    emit('safety_status', {
        'status': safety_status,
        'game_enabled': (safety_status == 'safe'),
        'areas': safety_info
    })
    print("Test: Person detected (REAR) - Game disabled")


@socketio.on('test_area_clear')
def handle_test_clear():
    """Test function to simulate area clear."""
    global tim240_alert, tim100_detected, tim150_detected
    tim240_alert = False
    tim100_detected = False
    tim150_detected = False
    safety_status, safety_info = get_combined_lidar_status()
    emit('safety_status', {
        'status': safety_status,
        'game_enabled': (safety_status == 'safe'),
        'areas': safety_info
    })
    print("Test: All areas clear - Game enabled")


@socketio.on('test_tim100_detected')
def handle_test_tim100():
    """Test function to simulate TiM100 detection."""
    global tim100_detected
    tim100_detected = True
    safety_status, safety_info = get_combined_lidar_status()
    emit('safety_status', {
        'status': safety_status,
        'game_enabled': (safety_status == 'safe'),
        'areas': safety_info
    })
    print("Test: TiM100 detected (LEFT) - Game disabled")


@socketio.on('test_tim150_detected')
def handle_test_tim150():
    """Test function to simulate TiM150 detection."""
    global tim150_detected
    tim150_detected = True
    safety_status, safety_info = get_combined_lidar_status()
    emit('safety_status', {
        'status': safety_status,
        'game_enabled': (safety_status == 'safe'),
        'areas': safety_info
    })
    print("Test: TiM150 detected (RIGHT) - Game disabled")


@socketio.on('set_credits')
def handle_set_credits(data):
    """Admin: Set credits directly."""
    global credits, ser
    try:
        new_credits = int(data.get('credits', 0))
        if new_credits < 0:
            new_credits = 0
        
        # Send command to Arduino
        if ser and not ser.closed:
            cmd = f"SET_CREDITS:{new_credits}\n".encode()
            ser.write(cmd)
            ser.flush()
            print(f"Admin: Set credits to {new_credits}")
            # Arduino will send back CREDITS: message, which will update our variable
        else:
            # Fallback: update directly if Arduino not available
            with credits_lock:
                credits = new_credits
            socketio.emit('credit_status', {
                'credits': credits,
                'changed': True
            })
    except (ValueError, TypeError) as e:
        print(f"Error setting credits: {e}")


@socketio.on('add_credits')
def handle_add_credits(data):
    """Admin: Add credits."""
    global credits, ser
    try:
        add_amount = int(data.get('credits', 0))
        if add_amount < 0:
            add_amount = 0
        
        # Send command to Arduino
        if ser and not ser.closed:
            cmd = f"ADD_CREDITS:{add_amount}\n".encode()
            ser.write(cmd)
            ser.flush()
            print(f"Admin: Adding {add_amount} credits")
            # Arduino will send back CREDITS: message, which will update our variable
        else:
            # Fallback: update directly if Arduino not available
            with credits_lock:
                credits += add_amount
            socketio.emit('credit_status', {
                'credits': credits,
                'changed': True
            })
    except (ValueError, TypeError) as e:
        print(f"Error adding credits: {e}")


@socketio.on('request_credits')
def handle_request_credits():
    """Request current credit status."""
    with credits_lock:
        emit('credit_status', {
            'credits': credits,
            'changed': False
        })


def start_serial_thread():
    """Start the serial reader thread."""
    global serial_running
    serial_running = True
    thread = Thread(target=serial_reader_thread, daemon=True)
    thread.start()
    # Start LiDAR status reader in parallel
    global lidar_thread
    lidar_thread = Thread(target=lidar_reader_thread, daemon=True)
    lidar_thread.start()
    return thread


if __name__ == '__main__':
    print("=" * 60)
    print("SICK7 - Arduino GPIO Control + Web Visualization + Credit Tracking")
    print("=" * 60)
    print("Credit System: 2 PBT hits = 1 credit deducted")
    print("LiDAR Safety: DISABLED when credits == 0")
    print("=" * 60)
    print(f"Serial port: {SERIAL_PORT} @ {BAUD} baud")
    print(f"Samples per second: {SAMPLES_PER_SEC}")
    print(f"Arcade Interface (Arduino GPIO):")
    print(f"  Arduino Pin 6: Press START signal (Active HIGH, 5V output)")
    print(f"  Arduino Pin 5: Press ACTIVE signal (Active LOW, 0V output)")
    print(f"Pulse Mapping: HIGH peak → SHORT pulse (INVERTED)")
    print(f"Peak Range: {A_MIN}-{A_MAX} ADC → Pulse Range: {W_MIN_MS}-{W_MAX_MS}ms")
    print(f"Trigger threshold: {TRIGGER_THRESHOLD} ADC counts")
    print(f"Web server: http://{HOST}:{PORT}")
    print("=" * 60)
    
    # Start serial reader thread (includes GPIO pulse generation)
    start_serial_thread()
    
    try:
        # Run Flask app
        socketio.run(app, host=HOST, port=PORT, debug=DEBUG, allow_unsafe_werkzeug=True)
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

