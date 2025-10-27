#!/bin/bash
# SICK7 LiDAR Monitoring System Startup Script
# Starts only the LiDAR monitoring system (no PBT)

echo "=========================================="
echo "SICK7 LiDAR Monitoring System"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    echo "Then: source venv/bin/activate"
    echo "Then: pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import flask, flask_socketio, serial" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Required packages not installed!"
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Check if Arduino is connected
echo "Checking Arduino connection..."
if [ ! -e "/dev/ttyUSB0" ] && [ ! -e "/dev/ttyACM0" ]; then
    echo "WARNING: No Arduino detected on /dev/ttyUSB0 or /dev/ttyACM0"
    echo "LiDAR monitoring will start but may not work properly"
fi

# Start LiDAR monitoring system
echo "Starting LiDAR monitoring system..."
echo "Web interface: http://localhost:5001"
echo "WebSocket: ws://localhost:5001"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="

python3 lidar_monitor.py
