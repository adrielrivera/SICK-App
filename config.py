"""
Configuration file for SICK PBT Sensor Web App
Modify these settings as needed for your setup
"""

# ============================================
# Serial Communication Settings
# ============================================
SERIAL_PORT = "/dev/ttyUSB0"  # Change to your Arduino's serial port
BAUD = 115200                  # Baud rate (must match Arduino)
SAMPLES_PER_SEC = 800         # Expected sample rate from Arduino

# ============================================
# Signal Processing Parameters
# ============================================
# Envelope detection
ENVELOPE_ALPHA = 0.12         # Envelope filter coefficient (0-1, lower = smoother)
TRIGGER_THRESHOLD = 60        # Trigger level for peak detection (ADC counts)

# Baseline tracking
BASELINE_ALPHA = 0.001        # Baseline tracking coefficient (0-1, lower = more stable)

# ============================================
# Web Server Settings
# ============================================
HOST = '0.0.0.0'              # Listen on all interfaces (use '127.0.0.1' for localhost only)
PORT = 5000                   # Web server port
SECRET_KEY = 'sick-capstone-secret'  # Change this for production!
DEBUG = False                 # Set to True for development

# ============================================
# Data Buffer Settings
# ============================================
BUFFER_SIZE = 4000           # Maximum samples to keep in memory (5 sec at 800 Hz)
EMIT_INTERVAL = 0.05         # How often to send data to clients (seconds, 0.05 = 20 Hz)

# ============================================
# Chart Display Settings
# ============================================
MAX_DISPLAY_POINTS = 4000    # Maximum points to display on chart
ADC_MIN = 0                  # Minimum ADC value
ADC_MAX = 1023              # Maximum ADC value (10-bit ADC)

