#!/bin/bash

# Performance Monitoring Script for SICK Sensor System
# Run this to check if your Raspberry Pi can handle the load

echo "========================================"
echo "  SICK System Performance Monitor"
echo "========================================"
echo ""

# Check Raspberry Pi model
if [ -f /proc/device-tree/model ]; then
    MODEL=$(cat /proc/device-tree/model)
    echo "📱 Raspberry Pi Model: $MODEL"
else
    echo "📱 System: $(uname -m)"
fi
echo ""

# Check CPU info
echo "🖥️  CPU Information:"
CORES=$(nproc)
echo "   CPU Cores: $CORES"
CPU_FREQ=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq 2>/dev/null)
if [ ! -z "$CPU_FREQ" ]; then
    echo "   Current Frequency: $((CPU_FREQ / 1000)) MHz"
fi
echo ""

# Check Memory
echo "💾 Memory Information:"
free -h | grep -E "Mem|Swap"
echo ""

# Check Temperature
echo "🌡️  Temperature:"
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
    TEMP_C=$((TEMP / 1000))
    echo "   CPU: ${TEMP_C}°C"
    if [ $TEMP_C -gt 70 ]; then
        echo "   ⚠️  WARNING: High temperature! Add cooling!"
    elif [ $TEMP_C -gt 80 ]; then
        echo "   🔥 CRITICAL: CPU throttling likely!"
    fi
else
    echo "   Temperature sensor not found"
fi
echo ""

# Check USB devices (sensors)
echo "🔌 USB Devices (Sensors):"
ls /dev/ttyUSB* 2>/dev/null || echo "   No USB serial devices found"
ls /dev/ttyACM* 2>/dev/null
echo ""

# Check running processes
echo "⚙️  SICK-related Processes:"
ps aux | grep -E "python3.*(app|pbt|sensor)" | grep -v grep || echo "   No SICK processes running"
echo ""

# Check CPU usage
echo "📊 Current CPU Usage:"
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print "   CPU Load: " 100 - $1 "%"}'
echo ""

# Check network connections
echo "🌐 Network Connections:"
netstat -tlnp 2>/dev/null | grep -E ":5000|:5001|:5002|:21" || echo "   No SICK web services running"
echo ""

# Check for throttling (Pi only)
if command -v vcgencmd &> /dev/null; then
    echo "⚡ Throttling Status:"
    THROTTLE=$(vcgencmd get_throttled)
    echo "   $THROTTLE"
    if [[ "$THROTTLE" == *"0x0"* ]]; then
        echo "   ✅ No throttling detected"
    else
        echo "   ⚠️  WARNING: System has been throttled!"
    fi
    echo ""
fi

# Recommendations
echo "========================================"
echo "  💡 Recommendations:"
echo "========================================"
echo ""

# Check RAM
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
if [ $TOTAL_RAM -lt 1024 ]; then
    echo "⚠️  WARNING: Low RAM ($TOTAL_RAM MB)"
    echo "   - Raspberry Pi 4 with 2GB+ recommended"
elif [ $TOTAL_RAM -lt 2048 ]; then
    echo "⚠️  RAM is adequate but may be tight ($TOTAL_RAM MB)"
    echo "   - Consider Pi 4 with 4GB for better performance"
else
    echo "✅ RAM is adequate ($TOTAL_RAM MB)"
fi
echo ""

# Check cores
if [ $CORES -lt 4 ]; then
    echo "⚠️  WARNING: Limited CPU cores ($CORES)"
    echo "   - Raspberry Pi 4 (quad-core) recommended"
else
    echo "✅ CPU core count is good ($CORES cores)"
fi
echo ""

# Check temperature
if [ ! -z "$TEMP_C" ]; then
    if [ $TEMP_C -gt 70 ]; then
        echo "🔥 Add cooling immediately!"
        echo "   - Install heatsink and fan"
        echo "   - Ensure good ventilation"
    else
        echo "✅ Temperature is acceptable"
    fi
fi
echo ""

echo "========================================"
echo "  📈 Load Testing Commands:"
echo "========================================"
echo ""
echo "1. Monitor in real-time:"
echo "   watch -n 1 'top -b -n 1 | head -20'"
echo ""
echo "2. CPU stress test:"
echo "   stress --cpu $CORES --timeout 60s"
echo ""
echo "3. Check for dropped samples:"
echo "   tail -f /var/log/sick-pbt.log"
echo ""
echo "4. Network performance:"
echo "   iftop -i wlan0"
echo ""

echo "💡 See ARCHITECTURE_CONCERNS.md for optimization tips!"
echo ""

