#!/bin/bash
# Start the PBT-only system (no LiDAR, no credit tracking)

echo "=========================================="
echo "SICK7 PBT-Only System"
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

# Run the PBT-only app
echo "Starting SICK7 PBT-Only System..."
echo "Web interface: http://localhost:5000"
echo "Features: PBT sensor + GPIO control (no LiDAR, no credit tracking)"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="

python3 app_pbt_only.py
