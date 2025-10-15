#!/bin/bash
# Start the combined SICK PBT Sensor app with web interface and GPIO pulse output

# Make sure pigpio daemon is running
echo "Starting pigpio daemon..."
sudo systemctl start pigpiod
sleep 1

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the combined app
echo "Starting SICK PBT Combined App..."
python3 app_combined.py

