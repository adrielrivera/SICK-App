"""
Configuration file for SICK LiDAR Monitoring System
Separate configuration for LiDAR-only monitoring
"""
import threading

# ============================================
# Serial Communication Settings
# ============================================
SERIAL_PORT = "/dev/ttyUSB0"  # Change to your Arduino's serial port
BAUD = 115200                  # Baud rate (must match Arduino)

# ============================================
# Web Server Settings
# ============================================
HOST = '0.0.0.0'              # Listen on all interfaces
PORT = 5001                    # Different port from PBT system (5000)
SECRET_KEY = 'sick-lidar-secret'  # Different secret key
DEBUG = False                  # Set to True for development

# ============================================
# LiDAR Monitoring Settings
# ============================================
STATUS_EMIT_INTERVAL = 0.5     # How often to emit status updates (seconds)
MAX_MESSAGES_PER_READ = 20     # Max Arduino messages to read per loop
SERIAL_TIMEOUT = 1.0           # Serial read timeout (seconds)

# ============================================
# Threading
# ============================================
Thread = threading.Thread
