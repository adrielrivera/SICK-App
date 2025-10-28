#!/bin/bash
# SICK7 PBT Scoring Tester Startup Script
# Starts the PBT testing system for scoring validation

echo "=========================================="
echo "SICK7 PBT Scoring Tester"
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
python3 -c "import flask, flask_socketio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Required packages not installed!"
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Start PBT tester system
echo "Starting PBT Scoring Tester..."
echo "Web interface: http://localhost:5002"
echo ""
echo "Features:"
echo "  • Test single peak values"
echo "  • Test peak ranges (24-60)"
echo "  • Simulate complete hit sequences"
echo "  • Visual scoring feedback"
echo "  • Real-time pulse width calculation"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="

python3 pbt_tester.py
