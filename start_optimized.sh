#!/bin/bash

# Optimized Startup Script for Multi-Sensor System
# This script starts services with proper priorities and CPU pinning

echo "=========================================="
echo "   SICK Sensors - Optimized Startup"
echo "=========================================="
echo ""

# Check if running as root (needed for nice values < 0)
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Running without root - cannot set high priorities"
    echo "   For best performance, run: sudo ./start_optimized.sh"
    echo ""
fi

# Check if on Raspberry Pi
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model)
    echo "📱 Detected: $MODEL"
else
    echo "📱 Not running on Raspberry Pi"
fi
echo ""

# Check temperature
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
    TEMP_C=$((TEMP / 1000))
    echo "🌡️  CPU Temperature: ${TEMP_C}°C"
    if [ $TEMP_C -gt 80 ]; then
        echo "🔥 CRITICAL: Temperature too high! Add cooling!"
        echo "Aborting startup..."
        exit 1
    elif [ $TEMP_C -gt 70 ]; then
        echo "⚠️  WARNING: Temperature is high. Consider adding cooling."
    fi
fi
echo ""

# Check available memory
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
AVAIL_RAM=$(free -m | awk '/^Mem:/{print $7}')
echo "💾 Memory: ${AVAIL_RAM}MB available of ${TOTAL_RAM}MB total"
if [ $AVAIL_RAM -lt 200 ]; then
    echo "⚠️  WARNING: Low available memory!"
fi
echo ""

# Kill existing instances
echo "🔄 Stopping existing services..."
pkill -f "python3.*app.py" 2>/dev/null
pkill -f "python3.*test_mode.py" 2>/dev/null
sleep 1

# Create log directory
mkdir -p logs

# Start services with optimization
echo ""
echo "🚀 Starting services..."
echo ""

# Get number of CPU cores
CORES=$(nproc)
echo "   Available CPU cores: $CORES"

# Service 1: PBT Sensor (HIGH PRIORITY, PINNED TO CORE 0)
if [ "$EUID" -eq 0 ]; then
    echo "   ⚡ Starting PBT sensor (high priority, pinned to core 0)..."
    taskset -c 0 nice -n -10 python3 app.py > logs/pbt.log 2>&1 &
    PBT_PID=$!
    echo "      PID: $PBT_PID"
else
    echo "   ⚡ Starting PBT sensor (normal priority)..."
    python3 app.py > logs/pbt.log 2>&1 &
    PBT_PID=$!
    echo "      PID: $PBT_PID"
fi

sleep 2

# Check if started successfully
if ps -p $PBT_PID > /dev/null; then
    echo "      ✅ PBT sensor started"
else
    echo "      ❌ Failed to start PBT sensor"
    echo "      Check logs/pbt.log for errors"
fi

echo ""

# Service 2: Additional sensors (when ready)
# Uncomment when you add PMT, GM, etc.

# echo "   📡 Starting PMT sensor..."
# PORT=5001 python3 app_pmt.py > logs/pmt.log 2>&1 &
# PMT_PID=$!
# echo "      PID: $PMT_PID"

# echo "   📊 Starting GM counter..."
# PORT=5002 python3 app_gm.py > logs/gm.log 2>&1 &
# GM_PID=$!
# echo "      PID: $GM_PID"

echo ""
echo "=========================================="
echo "   📊 Status"
echo "=========================================="
echo ""

# Show process info
echo "Running processes:"
ps aux | grep -E "python3.*(app|sensor)" | grep -v grep | awk '{printf "   PID: %-6s CPU: %-5s MEM: %-5s CMD: %s\n", $2, $3"%", $4"%", $11}'

echo ""

# Get IP address
IP=$(hostname -I | awk '{print $1}')
echo "🌐 Access web interface at:"
echo "   Local:  http://localhost:5000"
if [ ! -z "$IP" ]; then
    echo "   Network: http://$IP:5000"
fi

echo ""
echo "📋 Useful commands:"
echo "   Monitor logs:  tail -f logs/pbt.log"
echo "   Monitor CPU:   htop"
echo "   Stop all:      pkill -f 'python3.*app.py'"
echo "   Performance:   ./monitor_performance.sh"
echo ""

# Start monitoring in background
if [ "$1" == "--monitor" ]; then
    echo "📊 Starting performance monitoring..."
    ./monitor_performance.sh
fi

echo "=========================================="
echo ""

