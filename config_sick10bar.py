"""
Configuration file for SICK 10 Bar PBT Sensor
Optimized based on oscilloscope measurements

SICK Sensor Characteristics (from scope):
- Baseline: 1.88V (~385 ADC counts)
- Peak: 2.96V (~607 ADC counts) 
- Amplitude: ~1.1V (~222 ADC counts)
- Pulse duration: ~700ms
- Output impedance: High (use 100kΩ input resistor)
"""

# ============================================
# Serial Communication Settings
# ============================================
SERIAL_PORT = "/dev/ttyUSB0"
BAUD = 115200
SAMPLES_PER_SEC = 800

# ============================================
# Signal Processing Parameters (SICK 10 Bar Optimized)
# ============================================
# With SICK sensor range of ~222 ADC counts total,
# and Arduino code re-centering around 512:
# - Quiet baseline: ~512
# - Typical impact: 512 + 50 to 150 = 562 to 662
# - Strong impact: 512 + 150 to 222 = 662 to 734

# Envelope detection
ENVELOPE_ALPHA = 0.08        # Lower for smoother envelope (SICK pulses are ~700ms)
TRIGGER_THRESHOLD = 40       # Start conservative, tune based on testing

# Baseline tracking
BASELINE_ALPHA = 0.0005      # Very stable baseline (SICK sensor has good stability)

# ============================================
# Web Server Settings
# ============================================
HOST = '0.0.0.0'
PORT = 5000
SECRET_KEY = 'sick-capstone-secret'
DEBUG = False

# ============================================
# Data Buffer Settings
# ============================================
BUFFER_SIZE = 4000           # 5 seconds at 800 Hz
EMIT_INTERVAL = 0.05         # 20 Hz update rate

# ============================================
# Chart Display Settings
# ============================================
MAX_DISPLAY_POINTS = 4000
ADC_MIN = 0
ADC_MAX = 1023

# ============================================
# SICK 10 Bar Specific Notes
# ============================================
# 
# Pulse Characteristics:
# - Duration: ~700ms (much longer than simulated hits)
# - Rise time: Fast (~50ms to peak)
# - Decay: Exponential (~650ms back to baseline)
#
# The ENVELOPE_ALPHA of 0.08 is lower than default (0.12) because
# SICK pulses are longer. This gives smoother envelope tracking.
#
# The TRIGGER_THRESHOLD of 40 is conservative. You may need to:
# - INCREASE (50-80) if you get false triggers from vibration
# - DECREASE (20-35) if you're missing weak impacts
#
# GPIO Pulse Mapping:
# The existing mapping in app_combined.py should work:
# - A_MIN = 80, A_MAX = 700
# - W_MIN_MS = 60, W_MAX_MS = 1500
#
# With SICK sensor range (~222 counts above baseline):
# - Weak impact: envelope ~550 → pulse ~300ms
# - Medium impact: envelope ~650 → pulse ~800ms  
# - Strong impact: envelope ~734 → pulse ~1100ms
#
# Calibration Tips:
# 1. Let system run for 10 seconds without impacts
# 2. Baseline should stabilize around 512 ± 5
# 3. Tap sensor - should see clean spikes
# 4. Check console: "Pulse #X: Peak=XXX → XXX ms"
# 5. Tune TRIGGER_THRESHOLD if needed
#

