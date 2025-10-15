#!/bin/bash
# Start the combined SICK PBT Sensor app with web interface and GPIO pulse output

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "WARNING: No virtual environment found"
fi

# Check if pigpio module is installed
if ! python3 -c "import pigpio" 2>/dev/null; then
    echo "pigpio module not found. Installing..."
    pip install pigpio
fi

# Make sure pigpio daemon is running
echo "Starting pigpio daemon..."
sudo systemctl start pigpiod
sleep 1

# Check if daemon started successfully
if ! systemctl is-active --quiet pigpiod; then
    echo "WARNING: pigpiod failed to start. GPIO pulses will be disabled."
    echo "Try: sudo apt-get install pigpio"
fi

# Run the combined app
echo "Starting SICK PBT Combined App..."
python3 app_combined.py

