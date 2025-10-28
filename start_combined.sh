#!/bin/bash
# Start the combined SICK7 app with PBT sensor + LiDAR monitoring + GPIO control

echo "=========================================="
echo "SICK7 Unified System (PBT + LiDAR + GPIO)"
echo "=========================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "ERROR: Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    echo "Then: source venv/bin/activate"
    echo "Then: pip install -r requirements.txt"
    exit 1
fi

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
    echo "System will start but may not work properly"
fi

# Run the combined app
echo "Starting SICK7 Unified System..."
echo "Web interface: http://localhost:5000"
echo "Features: PBT sensor + LiDAR monitoring + GPIO control"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="

python3 app_combined.py

