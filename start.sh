#!/bin/bash

# SICK PBT Sensor Web App - Start Script
# This script starts the Flask web application

echo "=========================================="
echo "   SICK PBT Sensor Web App"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✓ Virtual environment found"
    source venv/bin/activate
else
    echo "⚠ No virtual environment found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✓ Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if serial port exists
if [ ! -e "/dev/ttyUSB0" ]; then
    echo "⚠ Warning: /dev/ttyUSB0 not found"
    echo "Available serial ports:"
    ls /dev/tty* 2>/dev/null | grep -E "USB|ACM" || echo "  None found"
    echo ""
    echo "Edit app.py to set the correct SERIAL_PORT"
    echo ""
fi

# Start the app
echo "Starting web server..."
echo "Access the app at: http://localhost:5000"
echo "Or from another device: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 app.py

