#!/bin/bash
# Start PBT + LiDAR system with Credit Tracking
# Credit system: 2 PBT hits = 1 credit deducted
# LiDAR safety disabled when credits == 0

echo "=========================================="
echo "Starting PBT + LiDAR System with Credit Tracking"
echo "=========================================="

set -e

# Dependencies
echo "Checking Python packages..."
python3 - <<'PY'
import sys
missing = []
for m in ["flask", "flask_socketio", "serial"]:
    try:
        __import__(m)
    except Exception:
        missing.append(m)
if missing:
    print("MISSING:"+",".join(missing))
    sys.exit(1)
PY

if [ $? -ne 0 ]; then
  echo "Installing missing packages..."
  pip3 install flask flask-socketio pyserial
fi

# Port hints
if [ -e "/dev/ttyUSB0" ]; then echo "PBT Arduino (with credits): /dev/ttyUSB0"; fi
if [ -e "/dev/ttyUSB1" ]; then echo "LiDAR Arduino: /dev/ttyUSB1"; fi

echo ""
echo "Credit System Features:"
echo "  - 2 PBT hits = 1 credit deducted"
echo "  - LiDAR safety DISABLED when credits == 0"
echo "  - Use webapp to set/add credits (admin)"
echo ""

echo "Launching app_with_credits.py..."
exec python3 app_with_credits.py


