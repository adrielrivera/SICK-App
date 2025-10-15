"""
Optimized Configuration for Multi-Sensor Setup
Use this for better performance when running multiple sensors + web app on single Pi

To use: Copy this to config.py or import settings from here
"""

# ============================================
# Serial Communication Settings
# ============================================
SERIAL_PORT = "/dev/ttyUSB0"
BAUD = 115200
SAMPLES_PER_SEC = 800

# ============================================
# Signal Processing Parameters  
# (Keep these - they're optimized)
# ============================================
ENVELOPE_ALPHA = 0.12
TRIGGER_THRESHOLD = 60
BASELINE_ALPHA = 0.001

# ============================================
# Web Server Settings
# ============================================
HOST = '0.0.0.0'
PORT = 5000
SECRET_KEY = 'sick-capstone-secret'  # Change in production!
DEBUG = False

# ============================================
# PERFORMANCE OPTIMIZATIONS
# ============================================

# Reduced buffer for lower memory usage
BUFFER_SIZE = 2000           # 2.5 seconds @ 800 Hz (was 4000)

# Slower update rate to reduce CPU load
EMIT_INTERVAL = 0.1          # 10 Hz updates (was 0.05 = 20 Hz)

# Limit simultaneous web clients
MAX_CLIENTS = 10             # Reject connections beyond this

# Chart display settings (less data = better performance)
MAX_DISPLAY_POINTS = 2000    # Was 4000

# ADC range
ADC_MIN = 0
ADC_MAX = 1023

# ============================================
# MULTI-SENSOR CONFIGURATION
# ============================================

# Enable/disable sensors (set to False to disable)
ENABLE_PBT = True
ENABLE_PMT = False           # Set True when PMT is ready
ENABLE_GM = False            # Set True when GM counter is ready

# Sensor ports (if using multiple)
PBT_PORT = 5000
PMT_PORT = 5001
GM_PORT = 5002

# ============================================
# RESOURCE MANAGEMENT
# ============================================

# Thread priorities (nice values: -20 to 19, lower = higher priority)
PBT_PRIORITY = -10           # High priority (real-time critical)
WEB_PRIORITY = 0             # Normal priority
FTP_PRIORITY = 10            # Low priority (not time-critical)

# CPU affinity (which cores to use) - Pi 4 has cores 0-3
PBT_CPU_CORES = [0]          # Pin PBT to core 0
WEB_CPU_CORES = [1, 2, 3]    # Web app can use cores 1-3

# Memory limits
MAX_BUFFER_MEMORY_MB = 50    # Maximum memory for data buffers

# ============================================
# MONITORING & LOGGING
# ============================================

# Enable performance monitoring
ENABLE_MONITORING = True

# Log dropped samples
LOG_DROPPED_SAMPLES = True

# Performance metrics logging interval (seconds)
METRICS_INTERVAL = 10

# Log file paths
LOG_FILE = '/var/log/sick-sensors.log'
METRICS_FILE = '/var/log/sick-metrics.log'

# ============================================
# FAILSAFE SETTINGS
# ============================================

# Automatic restart on error
AUTO_RESTART = True

# Maximum restarts before giving up
MAX_RESTARTS = 5

# Restart cooldown (seconds)
RESTART_COOLDOWN = 10

# Temperature monitoring (Celsius)
TEMP_WARNING = 70            # Log warning
TEMP_CRITICAL = 80           # Throttle or shutdown

# ============================================
# DEVELOPER NOTES
# ============================================

"""
Performance Tuning Guide:

1. Low CPU (< 50%): 
   - Increase EMIT_INTERVAL to 0.05 (20 Hz)
   - Increase BUFFER_SIZE to 4000

2. High CPU (> 80%):
   - Increase EMIT_INTERVAL to 0.2 (5 Hz)
   - Decrease BUFFER_SIZE to 1000
   - Reduce MAX_CLIENTS to 5

3. Memory Issues:
   - Reduce BUFFER_SIZE
   - Reduce MAX_CLIENTS
   - Check for memory leaks

4. Dropped Samples:
   - Increase PBT_PRIORITY to -15
   - Pin PBT to dedicated core
   - Check for blocking operations

Monitoring:
   ./monitor_performance.sh - Check system status
   htop - Real-time process monitor
   journalctl -f - Live system logs
"""

