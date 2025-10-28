#!/bin/bash
# SICK7 Arduino PBT Simulator Startup Script
# Uploads the Arduino simulator code and provides instructions

echo "=========================================="
echo "SICK7 Arduino PBT Simulator"
echo "=========================================="

# Check if Arduino IDE is available
if ! command -v arduino-cli &> /dev/null; then
    echo "ERROR: arduino-cli not found!"
    echo "Please install Arduino CLI or use Arduino IDE"
    echo ""
    echo "To install arduino-cli:"
    echo "  curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh"
    echo ""
    echo "Or use Arduino IDE to upload arduino_pbt_simulator.ino"
    exit 1
fi

# Check if Arduino is connected
echo "Checking for Arduino..."
if ! arduino-cli board list | grep -q "ttyUSB\|ttyACM"; then
    echo "WARNING: No Arduino detected!"
    echo "Please connect Arduino and try again"
    echo ""
    echo "Expected ports: /dev/ttyUSB0 or /dev/ttyACM0"
    exit 1
fi

# Get Arduino port
ARDUINO_PORT=$(arduino-cli board list | grep -E "ttyUSB|ttyACM" | head -1 | awk '{print $1}')
echo "Arduino found on: $ARDUINO_PORT"

# Compile and upload
echo "Compiling Arduino simulator..."
arduino-cli compile --fqbn arduino:avr:uno SICK-App.ino

if [ $? -ne 0 ]; then
    echo "ERROR: Compilation failed!"
    exit 1
fi

echo "Uploading to Arduino..."
arduino-cli upload -p $ARDUINO_PORT --fqbn arduino:avr:uno SICK-App.ino

if [ $? -ne 0 ]; then
    echo "ERROR: Upload failed!"
    exit 1
fi

echo ""
echo "=========================================="
echo "Arduino Simulator Uploaded Successfully!"
echo "=========================================="
echo ""
echo "Oscilloscope Connections:"
echo "  Pin 3 (PWM) → Oscilloscope Channel 1 (PBT Waveform)"
echo "  Pin 6 (Digital) → Oscilloscope Channel 2 (Arcade Start)"
echo "  Pin 5 (Digital) → Oscilloscope Channel 3 (Arcade Active)"
echo "  GND → Oscilloscope Ground"
echo ""
echo "Expected Waveform:"
echo "  - Baseline: ~2.5V (512 ADC = 128 PWM)"
echo "  - Noise: ±0.1V random variation"
echo "  - Peaks: 0.5V to 2.5V spikes (30-100 ADC)"
echo "  - Frequency: 800Hz sampling rate"
echo ""
echo "Next Steps:"
echo "  1. Connect oscilloscope probes"
echo "  2. Start Pi tester: ./start_tester.sh"
echo "  3. Open web interface: http://localhost:5002"
echo "  4. Click 'Start Simulation' to begin"
echo ""
echo "The Arduino will now generate realistic PBT waveforms!"
echo "=========================================="
