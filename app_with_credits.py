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

# GPIO for credit add signal (falling edge to Arduino)
# WARNING: If GPIO pin has noise issues, set USE_GPIO_FOR_CREDITS = False to use serial only
USE_GPIO_FOR_CREDITS = False  # Set to False to disable GPIO credit adds (use serial only)
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    CREDIT_GPIO_PIN = 18  # GPIO18 (Physical Pin 12) - Credit add signal to Arduino Pin 2
except ImportError:
    GPIO_AVAILABLE = False
    USE_GPIO_FOR_CREDITS = False
    print("⚠️  RPi.GPIO not available - credit add signal disabled")

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

# Legacy variables (not used with OR gate, but kept to match app_combined.py)
tim100_detected = False
tim150_detected = False
tim240_alert = False

# Credit tracking system (shared between threads)
credits_lock = Lock()
credits = 0  # Current credit count (tracked from Arduino)
last_credit_deduction_time = 0  # Timestamp of last deduction (to ignore stale Arduino updates)
CREDIT_UPDATE_COOLDOWN = 0.5  # Ignore Arduino credit updates for 0.5s after deduction

# PBT hit counting (done on Pi, not Arduino)
pbt_hit_count = 0  # Count PBT hits (2 hits = 1 credit deducted)
HITS_PER_CREDIT = 2


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
    """Calculate pulse width from peak value - map 30-90 ADC to 55-10ms.
    
    Adjusted to match arcade machine's scoring (easier to get max score):
    - 30 ADC -> 55ms pulse -> 140 points (arcade)
    - 90 ADC -> 10ms pulse -> 500 points (arcade)
    """
    a_clamped = clamp(peak, A_MIN, min(A_MAX, 90))  # Cap at 90 for easier scoring
    
    # Map 30-90 ADC to 55-10ms pulse width to match arcade scoring
    # 30 ADC -> 55ms (140 points on arcade)
    # 90 ADC -> 10ms (500 points on arcade)
    # Linear mapping: width = 55 - (peak - 30) * 45 / 60
    width_ms = 55 - (a_clamped - 30) * (45 / 60)  # 30->55ms, 90->10ms
    
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
    """Read and display Arduino status messages."""
    global tim100_detected, tim150_detected
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
    """Get combined status from all LiDARs."""
    global lidar_person_detected, lidar_alarm_active

    if lidar_person_detected:
        return "DANGER", {
            'areas': ["ANY"]
        }
    else:
        return "SAFE", {
            'areas': []
        }


def lidar_reader_thread():
    """Background thread: read LiDAR alarm Arduino on ttyUSB1 and update person_detected."""
    global lidar_ser, lidar_person_detected, lidar_alarm_active, credits
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
                # Debug: Log all lines from LiDAR Arduino (can be commented out later)
                if line.startswith("CREDITS:") or "credit" in line.lower():
                    print(f"📥 [RAW] LiDAR Arduino line: '{line}'")
                    print(f"   Line length: {len(line)}, Starts with CREDITS: {line.startswith('CREDITS:')}")
                    print(f"   First 10 chars: '{line[:10] if len(line) >= 10 else line}'")
                    print(f"   repr: {repr(line)}")
                
                # Parse credit status updates from LiDAR Arduino (credit-specific addition) - CHECK FIRST
                # Use strip() to handle any whitespace issues
                stripped_line = line.strip()
                if stripped_line.startswith("CREDITS:"):
                    print(f"🔍 ENTERING CREDITS parsing block for line: '{line}' (stripped: '{stripped_line}')")
                    try:
                        global last_credit_deduction_time
                        current_time = time.time()
                        
                        print(f"   Step 1: Splitting line...")
                        credit_str = stripped_line.split(":", 1)[1].strip()
                        print(f"   Step 2: Parsing int from '{credit_str}'...")
                        new_credits = int(credit_str)
                        print(f"   Step 3: Got new_credits={new_credits}, checking cooldown...")
                        
                        # Check if we're in cooldown period after a deduction
                        time_since_deduction = current_time - last_credit_deduction_time
                        in_cooldown = (time_since_deduction < CREDIT_UPDATE_COOLDOWN) and (last_credit_deduction_time > 0)
                        
                        if in_cooldown:
                            print(f"   ⏸️  In cooldown ({time_since_deduction:.2f}s < {CREDIT_UPDATE_COOLDOWN}s) - ignoring Arduino update")
                            print(f"   Arduino says: {new_credits}, but we have: {credits} (deduction in progress)")
                            # Only accept if Arduino value matches our optimistic deduction
                            with credits_lock:
                                expected_credits = credits
                                if new_credits == expected_credits:
                                    print(f"   ✅ Arduino confirmed our deduction: {new_credits}")
                                    # Confirmed - clear cooldown
                                    last_credit_deduction_time = 0
                                elif new_credits > expected_credits:
                                    print(f"   ⚠️  Arduino has MORE credits ({new_credits}) than expected ({expected_credits})")
                                    print(f"   Possible: Credit add signal received, or Arduino out of sync")
                                    # Accept the higher value (might be legitimate add)
                                    old_credits = credits
                                    credits = new_credits
                                    last_credit_deduction_time = 0
                                else:
                                    print(f"   ⚠️  Arduino has LESS credits ({new_credits}) than expected ({expected_credits})")
                                    print(f"   Ignoring - might be stale update")
                                    # Don't update, keep our optimistic value
                                    new_credits = credits  # Use our value for emit
                        else:
                            print(f"   Step 4: Not in cooldown, updating normally...")
                            with credits_lock:
                                old_credits = credits
                                credits = max(0, new_credits)
                        # Calculate if credits changed (need to track old_credits properly)
                        old_credits_for_emit = credits  # Will be updated if we change credits
                        if in_cooldown:
                            # During cooldown, track old value before potential update
                            with credits_lock:
                                old_credits_for_emit = credits
                            # Then check if we updated
                            if new_credits == credits:
                                # Confirmed match - no change to emit
                                changed = False
                            elif new_credits > credits:
                                # Accepted higher value - changed
                                changed = True
                                old_credits_for_emit = credits  # Before update
                            else:
                                # Ignored - no change
                                changed = False
                        else:
                            # Normal update - use tracked old_credits
                            changed = old_credits != credits
                        
                        print(f"   Step 6: changed={changed}, credits={credits}, old_credits={old_credits if not in_cooldown else old_credits_for_emit}")
                        if changed:
                            print(f"💰 Credits updated (from LiDAR Arduino): {credits} (was {old_credits_for_emit if in_cooldown else old_credits})")
                            if credits > (old_credits_for_emit if in_cooldown else old_credits) and not in_cooldown:
                                print(f"⚠️  WARNING: Credits INCREASED from Arduino! This shouldn't happen during deduction.")
                                print(f"   Possible causes: Arduino received credit add signal, or status update conflict")
                        else:
                            print(f"💰 Credits status received (unchanged): {credits}")
                        # Emit credit update to web clients (always emit, even if unchanged, to sync UI)
                        # Match the exact emit style used by safety_status (which works)
                        print(f"   Step 5: Emitting to socketio...")
                        socketio.emit('credit_status', {
                            'credits': credits,
                            'changed': changed
                        })
                        print(f"📤 Emitted credit_status to clients: credits={credits}, changed={changed}")
                    except Exception as e:
                        print(f"❌ Error in CREDITS parsing block: {type(e).__name__}: {e}")
                        print(f"   Line was: '{line}'")
                        import traceback
                        traceback.print_exc()
                elif line.startswith("LIDAR_STATUS:"):
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
    global ser, serial_running, baseline, envelope, sample_count, credits, last_credit_deduction_time
    global armed, peak, cap_end, pulse_count, lidar_ser
    
    print("GPIO control now handled by Arduino - no Pi GPIO needed!")
    print("Arduino will control arcade motherboard pins via Serial commands.")
    
    # Continuous GPIO credit pin monitoring - ensure it stays HIGH
    # CRITICAL: Always monitor, even if GPIO credit adds are disabled
    # This prevents the pin from floating and triggering false credit adds
    if GPIO_AVAILABLE:
        def monitor_credit_gpio():
            """Background task: continuously ensure credit GPIO pin stays HIGH"""
            last_check = time.time()
            last_warning = 0
            while serial_running:
                try:
                    current_time = time.time()
                    # Check every 50ms
                    if current_time - last_check >= 0.05:
                        pin_state = GPIO.input(CREDIT_GPIO_PIN)
                        if pin_state != GPIO.HIGH:
                            # Only warn once per second to avoid spam
                            if current_time - last_warning >= 1.0:
                                print(f"⚠️  GPIO credit pin went LOW! Correcting to HIGH...")
                                last_warning = current_time
                            GPIO.output(CREDIT_GPIO_PIN, GPIO.HIGH)
                            time.sleep(0.01)
                        last_check = current_time
                    time.sleep(0.02)  # Check every 20ms
                except Exception as e:
                    print(f"⚠️  Error in GPIO monitor: {e}")
                    time.sleep(0.1)
        
        # Start GPIO monitor in background
        import threading
        gpio_monitor_thread = threading.Thread(target=monitor_credit_gpio, daemon=True)
        gpio_monitor_thread.start()
        if USE_GPIO_FOR_CREDITS:
            print("✅ Started GPIO credit pin monitor (ensures pin stays HIGH, will pulse for credit adds)")
        else:
            print("✅ Started GPIO credit pin monitor (ensures pin stays HIGH, credit adds via serial only)")
    
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
    
    envelope = 0.0
    print(f"Baseline calibrated: {baseline:.1f} ADC counts")
    
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
        
        # Only process pulse generation if game is enabled
        # When disabled, keep system armed but continue reading serial data normally
        # Credit check is done separately - if no credits, we still track hits but don't deduct
        if game_enabled:
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
                    print(f"Pulse #{pulse_count}: Peak={peak:.1f} → {width_ms:.0f} ms")
                    print(f"  Mapping: Peak {peak:.1f} → Pulse {width_ms:.0f}ms (Range: {A_MIN}-{A_MAX} → {W_MIN_MS}-{W_MAX_MS}ms)")
                    
                    # Track PBT hits on Pi (2 hits = 1 credit deducted)
                    # This is credit-specific logic, doesn't affect core PBT/LiDAR logic
                    global pbt_hit_count
                    pbt_hit_count += 1
                    print(f"🎯 PBT Hit #{pulse_count}: hit_count={pbt_hit_count}/{HITS_PER_CREDIT}")
                    
                    # When 2 hits reached, deduct 1 credit from LiDAR Arduino
                    if pbt_hit_count >= HITS_PER_CREDIT:
                        pbt_hit_count = 0  # Reset counter
                        
                        # Check if credits available before deducting
                        global last_credit_deduction_time
                        with credits_lock:
                            current_credits_before = credits
                            if credits > 0:
                                # Optimistically update local credits (Arduino will confirm)
                                credits = max(0, credits - 1)
                                last_credit_deduction_time = time.time()
                                print(f"💸 Deducting credit: {current_credits_before} → {credits} (optimistic)")
                                print(f"   Set cooldown until: {last_credit_deduction_time + CREDIT_UPDATE_COOLDOWN:.2f}s")
                                
                                # Emit update immediately so UI shows deduction right away
                                socketio.emit('credit_status', {
                                    'credits': credits,
                                    'changed': True
                                })
                                print(f"📤 Emitted credit deduction immediately: {credits}")
                                
                                # Send DEDUCT_CREDIT command to LiDAR Arduino
                                deduct_success = False
                                try:
                                    if lidar_ser is None:
                                        print(f"⚠️  LiDAR Arduino serial not initialized")
                                    elif lidar_ser.closed:
                                        print(f"⚠️  LiDAR Arduino serial port is closed")
                                    else:
                                        # Check if port is writable
                                        try:
                                            lidar_ser.write(b"DEDUCT_CREDIT\n")
                                            lidar_ser.flush()
                                            print(f"📤 Sent DEDUCT_CREDIT command to Arduino")
                                            deduct_success = True
                                        except serial.SerialException as se:
                                            print(f"⚠️  Serial write error (may be temporary): {se}")
                                            # Try to reset the connection
                                            try:
                                                lidar_ser.close()
                                                time.sleep(0.1)
                                                lidar_ser = serial.Serial(LIDAR_SERIAL_PORT, LIDAR_BAUD, timeout=1)
                                                time.sleep(0.2)
                                                lidar_ser.reset_input_buffer()
                                                print(f"✅ Reconnected to LiDAR Arduino, retrying...")
                                                # Retry once
                                                lidar_ser.write(b"DEDUCT_CREDIT\n")
                                                lidar_ser.flush()
                                                print(f"📤 Sent DEDUCT_CREDIT command to Arduino (after reconnect)")
                                                deduct_success = True
                                            except Exception as retry_e:
                                                print(f"❌ Failed to reconnect to LiDAR Arduino: {retry_e}")
                                except Exception as e:
                                    print(f"❌ Error sending DEDUCT_CREDIT: {e}")
                                
                                # Only rollback if we couldn't send the command after retries
                                if not deduct_success:
                                    print(f"⚠️  Could not send DEDUCT_CREDIT to Arduino - keeping optimistic deduction")
                                    print(f"   Arduino will sync when it sends next CREDITS: status")
                                    # Don't rollback - keep the optimistic deduction
                                    # The Arduino will eventually send its credit status and sync
                                    # This prevents double-deduction if the command actually went through
                            else:
                                print(f"⚠️  Cannot deduct credit: credits already at 0")
                    
                    # CRITICAL: Ensure GPIO credit pin stays HIGH (idle) before/after PBT pulse
                    # This prevents false credit adds from noise or pin state changes
                    if GPIO_AVAILABLE and USE_GPIO_FOR_CREDITS:
                        try:
                            # Force pin HIGH before pulse (prevents any stray LOW signals)
                            GPIO.output(CREDIT_GPIO_PIN, GPIO.HIGH)
                            time.sleep(0.001)  # Brief stabilization
                            current_pin_state = GPIO.input(CREDIT_GPIO_PIN)
                            if current_pin_state != GPIO.HIGH:
                                print(f"⚠️  GPIO credit pin was LOW ({current_pin_state}) before pulse! Forced to HIGH...")
                                GPIO.output(CREDIT_GPIO_PIN, GPIO.HIGH)
                                time.sleep(0.01)  # Longer stabilization if correction needed
                        except Exception as e:
                            print(f"⚠️  Error checking GPIO credit pin: {e}")
                    
                    # Generate arcade button press using Arduino GPIO control
                    arcade_button_press(ser, width_ms)
                    
                    # CRITICAL: Immediately after pulse, ensure GPIO credit pin is HIGH
                    # Do this ASAP to prevent Arduino from detecting a falling edge
                    if GPIO_AVAILABLE and USE_GPIO_FOR_CREDITS:
                        try:
                            # Force HIGH immediately (don't check first - just set it)
                            GPIO.output(CREDIT_GPIO_PIN, GPIO.HIGH)
                            time.sleep(0.001)  # Brief stabilization
                            # Verify it's actually HIGH
                            current_pin_state = GPIO.input(CREDIT_GPIO_PIN)
                            if current_pin_state != GPIO.HIGH:
                                print(f"⚠️  GPIO credit pin went LOW ({current_pin_state}) after pulse! Forced to HIGH...")
                                GPIO.output(CREDIT_GPIO_PIN, GPIO.HIGH)
                                time.sleep(0.01)  # Longer stabilization if correction needed
                        except Exception as e:
                            print(f"⚠️  Error setting GPIO credit pin after pulse: {e}")
                    
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
    
    # Send initial safety status (use get_combined_lidar_status for accurate status)
    status_str, info = get_combined_lidar_status()
    emit('safety_status', {
        'status': status_str,
        'game_enabled': (status_str == 'SAFE'),
        'areas': info
    })
    
    # Send initial credit status
    with credits_lock:
        emit('credit_status', {
            'credits': credits,
            'changed': False
        })
        print(f"📤 Sent initial status to client: credits={credits}, lidar_status={status_str}")


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
    """Test function to simulate person detection (OR gate - any LiDAR)."""
    global lidar_person_detected
    lidar_person_detected = True
    safety_status, safety_info = get_combined_lidar_status()
    emit('safety_status', {
        'status': safety_status,
        'game_enabled': (safety_status == 'SAFE'),
        'areas': safety_info
    })
    print("Test: Person detected (ANY LiDAR via OR gate) - Game disabled")


@socketio.on('test_area_clear')
def handle_test_clear():
    """Test function to simulate area clear."""
    global lidar_person_detected
    lidar_person_detected = False
    safety_status, safety_info = get_combined_lidar_status()
    emit('safety_status', {
        'status': safety_status,
        'game_enabled': (safety_status == 'SAFE'),
        'areas': safety_info
    })
    print("Test: All areas clear - Game enabled")


@socketio.on('set_credits')
def handle_set_credits(data):
    """Admin: Set credits directly."""
    global credits, ser, pbt_hit_count, lidar_ser
    print(f"📥 Received set_credits event: {data}")
    try:
        new_credits = int(data.get('credits', 0))
        if new_credits < 0:
            new_credits = 0
        
        print(f"💰 Setting credits to: {new_credits}")
        
        # Update credits immediately (optimistic update)
        with credits_lock:
            credits = new_credits
        
        # Reset hit counter when credits are manually set
        pbt_hit_count = 0
        
        print(f"✅ Local credits updated to: {credits}")
        
        # Emit update to web clients immediately (use emit() for sender, socketio.emit() for all)
        try:
            emit('credit_status', {
                'credits': credits,
                'changed': True
            })
            print(f"📤 Emitted credit_status to sender via emit()")
        except Exception as e:
            print(f"⚠️  emit() failed: {e}, trying socketio.emit()")
        
        try:
            socketio.emit('credit_status', {
                'credits': credits,
                'changed': True
            })
            print(f"📤 Emitted credit_status to all clients via socketio.emit()")
        except Exception as e:
            print(f"❌ socketio.emit() failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Send command to LiDAR Arduino for synchronization
        if lidar_ser and not lidar_ser.closed:
            cmd = f"SET_CREDITS:{new_credits}\n".encode()
            lidar_ser.write(cmd)
            lidar_ser.flush()
            print(f"📤 Sent SET_CREDITS:{new_credits} to Arduino")
            # LiDAR Arduino will send back CREDITS: message, which will be read by lidar_reader_thread
            time.sleep(0.05)  # Small delay for Arduino to process
        else:
            print(f"⚠️  LiDAR serial not available, credits set locally only")
    except (ValueError, TypeError) as e:
        print(f"❌ Error setting credits: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Unexpected error in set_credits: {e}")
        import traceback
        traceback.print_exc()


@socketio.on('add_credits')
def handle_add_credits(data):
    """Admin: Add credits."""
    global credits, ser, pbt_hit_count, lidar_ser
    try:
        add_amount = int(data.get('credits', 0))
        if add_amount <= 0:
            print(f"⚠️  Invalid add_amount: {add_amount}")
            return
        
        # Reset hit counter when credits are manually added
        pbt_hit_count = 0
        
        # Get current credits for optimistic update
        with credits_lock:
            current_credits = credits
            new_credits = current_credits + add_amount
        
        print(f"💰 Adding {add_amount} credits (current: {current_credits}, new: {new_credits})")
        
        # CRITICAL: Sync Arduino with Pi's current credit count first, then add
        # This ensures Arduino and Pi are always in sync
        if lidar_ser and not lidar_ser.closed:
            # Step 1: Sync Arduino to current Pi value
            sync_cmd = f"SET_CREDITS:{current_credits}\n".encode()
            lidar_ser.write(sync_cmd)
            lidar_ser.flush()
            print(f"📤 Sent SET_CREDITS:{current_credits} to Arduino (sync)")
            time.sleep(0.05)  # Small delay for Arduino to process
            
            # Step 2: Add credits via hardware or serial
            if GPIO_AVAILABLE and USE_GPIO_FOR_CREDITS:
                print(f"📤 Sending {add_amount} credit add pulses via GPIO {CREDIT_GPIO_PIN}")
                # Ensure pin starts HIGH before pulsing
                current_pin_state = GPIO.input(CREDIT_GPIO_PIN)
                if current_pin_state != GPIO.HIGH:
                    print(f"⚠️  GPIO pin was {current_pin_state}, setting to HIGH first")
                    GPIO.output(CREDIT_GPIO_PIN, GPIO.HIGH)
                    time.sleep(0.05)  # Stabilize
                for i in range(add_amount):
                    # Ensure we start HIGH (idle state) and hold for stability
                    GPIO.output(CREDIT_GPIO_PIN, GPIO.HIGH)
                    time.sleep(0.02)  # 20ms HIGH (stable before falling edge)
                    # Falling edge: HIGH → LOW triggers Arduino interrupt
                    GPIO.output(CREDIT_GPIO_PIN, GPIO.LOW)
                    print(f"   [{i+1}/{add_amount}] GPIO pin LOW (falling edge)")
                    time.sleep(0.02)  # 20ms LOW (hold low for clean signal, prevents bounce)
                    # Return to HIGH (idle state)
                    GPIO.output(CREDIT_GPIO_PIN, GPIO.HIGH)
                    print(f"   [{i+1}/{add_amount}] GPIO pin HIGH (back to idle)")
                    time.sleep(0.1)  # 100ms delay between pulses (total 140ms per credit, well above 500ms debounce)
                    if (i + 1) % 5 == 0:
                        print(f"   Sent {i + 1}/{add_amount} pulses...")
                print(f"✅ Sent all {add_amount} credit add pulses")
                # Final verification
                final_state = GPIO.input(CREDIT_GPIO_PIN)
                if final_state != GPIO.HIGH:
                    print(f"⚠️  GPIO pin not HIGH after pulses! Setting to HIGH...")
                    GPIO.output(CREDIT_GPIO_PIN, GPIO.HIGH)
            else:
                # Fallback: use serial command if GPIO not available
                print(f"📤 Using serial ADD_CREDITS command (GPIO not available)")
                add_cmd = f"ADD_CREDITS:{add_amount}\n".encode()
                lidar_ser.write(add_cmd)
                lidar_ser.flush()
                print(f"📤 Sent ADD_CREDITS:{add_amount} to Arduino")
                time.sleep(0.05)
            
            # Step 3: Update local credits and wait for Arduino confirmation
            with credits_lock:
                credits = new_credits
        else:
            print(f"⚠️  LiDAR serial not available, updating locally only")
            # Update locally if no serial
            with credits_lock:
                credits = new_credits
        
        # Emit update to web clients immediately
        emit('credit_status', {
            'credits': new_credits,
            'changed': True
        })
        socketio.emit('credit_status', {
            'credits': new_credits,
            'changed': True
        })
        print(f"📤 Emitted credit update: {new_credits}")
        
        # Wait for LiDAR Arduino to process and send back CREDITS: message
        # The Arduino will send back the final value, which will sync everything
        time.sleep(0.2)  # Give Arduino time to process
    except (ValueError, TypeError) as e:
        print(f"❌ Error adding credits: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Error triggering GPIO credit signal: {e}")
        import traceback
        traceback.print_exc()


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
    if GPIO_AVAILABLE:
        print(f"Credit Add Signal (Hardware):")
        print(f"  Pi GPIO {CREDIT_GPIO_PIN} → Arduino Pin 2 (falling edge 5V→0V)")
    else:
        print(f"Credit Add Signal: Serial command (GPIO not available)")
    print(f"Pulse Mapping: HIGH peak → SHORT pulse (INVERTED)")
    print(f"Peak Range: {A_MIN}-{A_MAX} ADC → Pulse Range: {W_MIN_MS}-{W_MAX_MS}ms")
    print(f"Trigger threshold: {TRIGGER_THRESHOLD} ADC counts")
    print(f"Web server: http://{HOST}:{PORT}")
    print("=" * 60)
    
    # Initialize GPIO for credit add signal
    # CRITICAL: Always set pin as OUTPUT and HIGH, even if not using GPIO for credit adds
    # This prevents the pin from floating and causing false triggers
    if GPIO_AVAILABLE:
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(CREDIT_GPIO_PIN, GPIO.OUT, initial=GPIO.HIGH)  # Start HIGH (idle state)
            GPIO.output(CREDIT_GPIO_PIN, GPIO.HIGH)  # Explicitly set HIGH
            time.sleep(0.1)  # Ensure stable HIGH state
            pin_state = GPIO.input(CREDIT_GPIO_PIN)
            print(f"✅ GPIO {CREDIT_GPIO_PIN} initialized and set to HIGH (idle state)")
            print(f"   Pin state verified: {pin_state == GPIO.HIGH} (value: {pin_state})")
            if USE_GPIO_FOR_CREDITS:
                print(f"   GPIO credit adds: ENABLED (will pulse pin for credit adds)")
            else:
                print(f"   GPIO credit adds: DISABLED (using serial commands only)")
                print(f"   Pin will stay HIGH to prevent false triggers")
            if pin_state != GPIO.HIGH:
                print(f"⚠️  WARNING: GPIO pin is not HIGH! Setting to HIGH again...")
                GPIO.output(CREDIT_GPIO_PIN, GPIO.HIGH)
                time.sleep(0.1)
                pin_state = GPIO.input(CREDIT_GPIO_PIN)
                print(f"   After correction: {pin_state == GPIO.HIGH} (value: {pin_state})")
        except Exception as e:
            print(f"⚠️  GPIO initialization failed: {e}")
            print("   Credit add will use serial commands instead")
            USE_GPIO_FOR_CREDITS = False
    
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
        # Cleanup GPIO
        if GPIO_AVAILABLE:
            try:
                GPIO.output(CREDIT_GPIO_PIN, GPIO.HIGH)  # Return to idle
                GPIO.cleanup()
                print("✅ GPIO cleaned up")
            except:
                pass
        # Send reset command to Arduino to reset GPIO pins
        try:
            if ser and not ser.closed:
                ser.write(b"RESET_GPIO\n")
                ser.flush()
        except:
            pass

