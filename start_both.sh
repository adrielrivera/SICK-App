#!/bin/bash
# SICK7 Combined System Startup Script
# Starts both PBT system and LiDAR monitoring system

echo "=========================================="
echo "SICK7 Combined System (PBT + LiDAR)"
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
    echo "Systems will start but may not work properly"
fi

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "Shutting down systems..."
    if [ ! -z "$PBT_PID" ]; then
        echo "Stopping PBT system (PID: $PBT_PID)..."
        kill $PBT_PID 2>/dev/null
    fi
    if [ ! -z "$LIDAR_PID" ]; then
        echo "Stopping LiDAR system (PID: $LIDAR_PID)..."
        kill $LIDAR_PID 2>/dev/null
    fi
    echo "All systems stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start PBT system in background
echo "Starting PBT system..."
python3 app_combined.py &
PBT_PID=$!
echo "PBT system started (PID: $PBT_PID)"

# Wait a moment for PBT system to initialize
sleep 2

# Start LiDAR monitoring system in background
echo "Starting LiDAR monitoring system..."
python3 lidar_monitor.py &
LIDAR_PID=$!
echo "LiDAR system started (PID: $LIDAR_PID)"

# Wait a moment for LiDAR system to initialize
sleep 2

echo ""
echo "=========================================="
echo "Both systems are running!"
echo "PBT Web interface: http://localhost:5000"
echo "LiDAR Web interface: http://localhost:5001"
echo "PBT WebSocket: ws://localhost:5000"
echo "LiDAR WebSocket: ws://localhost:5001"
echo ""
echo "Press Ctrl+C to stop both systems"
echo "=========================================="

# Wait for user interrupt
wait
