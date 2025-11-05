#!/bin/bash
# Start combined PBT + LiDAR (dual Arduino) system with Credit Tracking

echo "=========================================="
echo "Starting Combined PBT + LiDAR (Dual Arduino) with Credit Tracking"
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
if [ -e "/dev/ttyUSB0" ]; then echo "PBT Arduino: /dev/ttyUSB0"; fi
if [ -e "/dev/ttyUSB1" ]; then echo "LiDAR Arduino: /dev/ttyUSB1"; fi

echo "Launching app_with_credits.py (do not start lidar_webapp.py separately)"
exec python3 app_with_credits.py


