#!/usr/bin/env python3
"""
SICK7 - LiDAR Monitoring System
Pure LiDAR monitoring without PBT interference
Monitors TiM100/TiM150 detection and sends status to web app
"""
import time
import sys
import serial
from flask import Flask
from flask_socketio import SocketIO, emit
from config_lidar import *

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Serial connection
ser = None
serial_running = False

# LiDAR status tracking
tim100_detected = False
tim150_detected = False
tim240_alert = False  # For future TiM240 integration

# Statistics
message_count = 0
last_status_emit = 0


def read_arduino_messages(ser):
    """Read and process Arduino LiDAR status messages."""
    global tim100_detected, tim150_detected, message_count
    
    try:
        # Limit the number of lines read per call to prevent blocking
        lines_read = 0
        max_lines_per_call = 20
        
        while ser.in_waiting > 0 and lines_read < max_lines_per_call:
            line = ser.readline().decode(errors="ignore").strip()
            lines_read += 1
            
            # Skip raw PBT data (just numbers) - only process system messages
            if line and line.isdigit():
                continue  # Skip raw PBT sensor data
            
            # Process system messages
            if line and (line.startswith("#") or "TiM" in line or "LIDAR" in line):
                print(f"LiDAR Monitor: {line}")
                message_count += 1
                
                # Parse TiM1xx status from Arduino
                if line.startswith("# LIDAR_STATUS:"):
                    parts = line.split()
                    if len(parts) >= 4:
                        tim100_detected = "DETECTED" in parts[1]
                        tim150_detected = "DETECTED" in parts[3]
                        print(f"  Status Update: TiM100={tim100_detected}, TiM150={tim150_detected}")
                elif "TiM100 DETECTED" in line:
                    tim100_detected = True
                    print(f"  TiM100 DETECTED - Person on LEFT side")
                elif "TiM100 CLEAR" in line:
                    tim100_detected = False
                    print(f"  TiM100 CLEAR - LEFT side clear")
                elif "TiM150 DETECTED" in line:
                    tim150_detected = True
                    print(f"  TiM150 DETECTED - Person on RIGHT side")
                elif "TiM150 CLEAR" in line:
                    tim150_detected = False
                    print(f"  TiM150 CLEAR - RIGHT side clear")
                    
    except Exception as e:
        print(f"LiDAR Monitor Serial Error: {e}")
        pass  # Ignore serial read errors


def get_combined_lidar_status():
    """Get combined status from all LiDARs."""
    global tim240_alert, tim100_detected, tim150_detected
    
    if tim240_alert or tim100_detected or tim150_detected:
        unsafe_areas = []
        if tim240_alert: unsafe_areas.append("REAR")
        if tim100_detected: unsafe_areas.append("LEFT")
        if tim150_detected: unsafe_areas.append("RIGHT")
        
        return "DANGER", {
            'rear': tim240_alert,
            'left': tim100_detected,
            'right': tim150_detected,
            'areas': unsafe_areas
        }
    else:
        return "SAFE", {
            'rear': False,
            'left': False,
            'right': False,
            'areas': []
        }


def serial_reader_thread():
    """Background thread to read Arduino LiDAR messages."""
    global ser, serial_running, last_status_emit
    
    print("Initializing LiDAR monitoring serial connection...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
        time.sleep(0.2)
        ser.reset_input_buffer()
        print(f"LiDAR Monitor: Arduino connected on {SERIAL_PORT} @ {BAUD} baud")
        
        # Test connection by reading a few lines
        print("LiDAR Monitor: Testing Arduino connection...")
        for i in range(3):
            if ser.in_waiting > 0:
                line = ser.readline().decode(errors="ignore").strip()
                if line:
                    print(f"LiDAR Monitor Test read: '{line}'")
            time.sleep(0.5)
    except Exception as e:
        print(f"ERROR: Could not open serial port {SERIAL_PORT}: {e}", file=sys.stderr)
        serial_running = False
        return
    
    print("LiDAR Monitor: Starting continuous monitoring...")
    
    # Main reading loop
    while serial_running:
        now = time.time()
        
        # Read Arduino messages
        read_arduino_messages(ser)
        
        # Send status updates to web clients every 0.5 seconds
        if now - last_status_emit >= 0.5:
            safety_status, safety_info = get_combined_lidar_status()
            
            # Emit LiDAR status to all connected clients
            socketio.emit('lidar_status', {
                'tim100': tim100_detected,
                'tim150': tim150_detected,
                'tim240': tim240_alert,
                'combined': tim100_detected or tim150_detected or tim240_alert,
                'safety_status': safety_status,
                'safety_info': safety_info,
                'message_count': message_count
            })
            
            last_status_emit = now
        
        # Small delay to prevent excessive CPU usage
        time.sleep(0.01)
    
    # Cleanup
    if ser:
        ser.close()
    print("LiDAR Monitor: Serial reader thread stopped")


@app.route('/')
def index():
    """LiDAR monitoring status page."""
    from flask import render_template
    return render_template('lidar_monitor.html')


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('LiDAR Monitor: Client connected')
    
    # Send initial LiDAR status
    safety_status, safety_info = get_combined_lidar_status()
    emit('lidar_status', {
        'tim100': tim100_detected,
        'tim150': tim150_detected,
        'tim240': tim240_alert,
        'combined': tim100_detected or tim150_detected or tim240_alert,
        'safety_status': safety_status,
        'safety_info': safety_info,
        'message_count': message_count
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('LiDAR Monitor: Client disconnected')


@socketio.on('request_lidar_status')
def handle_lidar_status_request():
    """Send current LiDAR status to client."""
    safety_status, safety_info = get_combined_lidar_status()
    emit('lidar_status', {
        'tim100': tim100_detected,
        'tim150': tim150_detected,
        'tim240': tim240_alert,
        'combined': tim100_detected or tim150_detected or tim240_alert,
        'safety_status': safety_status,
        'safety_info': safety_info,
        'message_count': message_count
    })


@socketio.on('test_tim100_detected')
def handle_test_tim100():
    """Test function to simulate TiM100 detection."""
    global tim100_detected
    tim100_detected = True
    safety_status, safety_info = get_combined_lidar_status()
    emit('lidar_status', {
        'tim100': tim100_detected,
        'tim150': tim150_detected,
        'tim240': tim240_alert,
        'combined': tim100_detected or tim150_detected or tim240_alert,
        'safety_status': safety_status,
        'safety_info': safety_info,
        'message_count': message_count
    })
    print("LiDAR Monitor Test: TiM100 detected (LEFT)")


@socketio.on('test_tim150_detected')
def handle_test_tim150():
    """Test function to simulate TiM150 detection."""
    global tim150_detected
    tim150_detected = True
    safety_status, safety_info = get_combined_lidar_status()
    emit('lidar_status', {
        'tim100': tim100_detected,
        'tim150': tim150_detected,
        'tim240': tim240_alert,
        'combined': tim100_detected or tim150_detected or tim240_alert,
        'safety_status': safety_status,
        'safety_info': safety_info,
        'message_count': message_count
    })
    print("LiDAR Monitor Test: TiM150 detected (RIGHT)")


@socketio.on('test_tim240_detected')
def handle_test_tim240():
    """Test function to simulate TiM240 detection."""
    global tim240_alert
    tim240_alert = True
    safety_status, safety_info = get_combined_lidar_status()
    emit('lidar_status', {
        'tim100': tim100_detected,
        'tim150': tim150_detected,
        'tim240': tim240_alert,
        'combined': tim100_detected or tim150_detected or tim240_alert,
        'safety_status': safety_status,
        'safety_info': safety_info,
        'message_count': message_count
    })
    print("LiDAR Monitor Test: TiM240 detected (REAR)")


@socketio.on('test_all_clear')
def handle_test_clear():
    """Test function to simulate all areas clear."""
    global tim240_alert, tim100_detected, tim150_detected
    tim240_alert = False
    tim100_detected = False
    tim150_detected = False
    safety_status, safety_info = get_combined_lidar_status()
    emit('lidar_status', {
        'tim100': tim100_detected,
        'tim150': tim150_detected,
        'tim240': tim240_alert,
        'combined': tim100_detected or tim150_detected or tim240_alert,
        'safety_status': safety_status,
        'safety_info': safety_info,
        'message_count': message_count
    })
    print("LiDAR Monitor Test: All areas clear")


def start_serial_thread():
    """Start the serial reader thread."""
    global serial_running
    serial_running = True
    thread = Thread(target=serial_reader_thread, daemon=True)
    thread.start()
    return thread


if __name__ == '__main__':
    print("=" * 60)
    print("SICK7 stupid stupid 67676767")
    print("=" * 60)
    print(f"Serial port: {SERIAL_PORT} @ {BAUD} baud")
    print(f"Web server: http://{HOST}:{PORT}")
    print(f"WebSocket: ws://{HOST}:{PORT}")
    print("Monitoring: TiM100 (LEFT), TiM150 (RIGHT), TiM240 (REAR)")
    print("=" * 60)
    
    # Start serial reader thread
    start_serial_thread()
    
    try:
        # Run Flask app
        socketio.run(app, host=HOST, port=PORT, debug=DEBUG, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\nShutting down LiDAR Monitor...")
    finally:
        serial_running = False
        if ser:
            ser.close()
