# SICK7 Separate Systems Architecture

## Overview

The SICK7 system has been redesigned with **separate, independent systems** to avoid blocking issues and improve reliability:

- **PBT System** (`app_combined.py`) - Handles PBT sensor data and arcade control
- **LiDAR System** (`lidar_monitor.py`) - Handles LiDAR monitoring and safety status

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   PBT System    │    │  LiDAR System   │
│                 │    │                 │
│ app_combined.py │    │ lidar_monitor.py│
│ Port: 5000      │    │ Port: 5001      │
│ WebSocket: 5000 │    │ WebSocket: 5001 │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
            ┌────────▼────────┐
            │   Arduino       │
            │   Serial        │
            │   /dev/ttyUSB0  │
            └─────────────────┘
```

## 📁 File Structure

```
SICK7/SICK-App/
├── app_combined.py              # PBT system (port 5000)
├── lidar_monitor.py             # LiDAR system (port 5001)
├── config.py                    # PBT configuration
├── config_lidar.py              # LiDAR configuration
├── start_combined.sh            # Start PBT system only
├── start_lidar.sh               # Start LiDAR system only
├── start_both.sh                # Start both systems
├── templates/
│   ├── index.html               # PBT web interface
│   └── lidar_monitor.html       # LiDAR web interface
└── static/
    ├── css/style.css            # Shared styles
    └── js/main.js               # PBT JavaScript
```

## 🚀 Usage

### Start Individual Systems

```bash
# Start PBT system only
./start_combined.sh

# Start LiDAR system only
./start_lidar.sh
```

### Start Both Systems

```bash
# Start both systems simultaneously
./start_both.sh
```

### Web Interfaces

- **PBT System**: http://localhost:5000
- **LiDAR System**: http://localhost:5001

## 🔧 Configuration

### PBT System (`config.py`)
```python
SERIAL_PORT = "/dev/ttyUSB0"
BAUD = 115200
HOST = '0.0.0.0'
PORT = 5000
```

### LiDAR System (`config_lidar.py`)
```python
SERIAL_PORT = "/dev/ttyUSB0"
BAUD = 115200
HOST = '0.0.0.0'
PORT = 5001
```

## 📡 Communication

### Arduino Messages
Both systems read from the same Arduino serial port but process different message types:

**PBT System** processes:
- Raw PBT sensor data (numbers)
- PBT hit notifications
- Credit tracking messages

**LiDAR System** processes:
- TiM100/TiM150 detection messages
- LiDAR status updates
- Safety system messages

### WebSocket Events

**PBT System** (`ws://localhost:5000`):
- `sensor_data` - PBT waveform data
- `safety_status` - Combined safety status
- `test_person_detected` - Test functions

**LiDAR System** (`ws://localhost:5001`):
- `lidar_status` - Individual LiDAR status
- `test_tim100_detected` - Test functions
- `test_tim150_detected` - Test functions
- `test_tim240_detected` - Test functions

## 🛡️ Safety System

The safety system works across both systems:

1. **LiDAR System** monitors TiM100/TiM150/TiM240 detection
2. **PBT System** receives safety status and disables game when unsafe
3. Both systems can be tested independently

## 🔍 Debugging

### Check System Status
```bash
# Check if PBT system is running
curl http://localhost:5000

# Check if LiDAR system is running
curl http://localhost:5001

# Check WebSocket connections
# Use browser developer tools to inspect WebSocket messages
```

### Log Files
- PBT system logs to console
- LiDAR system logs to console
- Both systems can run simultaneously without conflicts

## 🚨 Troubleshooting

### Common Issues

1. **Port Conflicts**
   - PBT system uses port 5000
   - LiDAR system uses port 5001
   - Make sure both ports are available

2. **Serial Port Access**
   - Both systems need access to `/dev/ttyUSB0`
   - Only one system should read at a time to avoid conflicts

3. **WebSocket Connection Issues**
   - Check firewall settings
   - Verify ports are open
   - Check browser console for errors

### Restart Systems
```bash
# Stop all systems
pkill -f "python3.*app_combined.py"
pkill -f "python3.*lidar_monitor.py"

# Start both systems
./start_both.sh
```

## 📈 Benefits

1. **No Blocking Issues** - LiDAR monitoring runs independently
2. **Better Reliability** - PBT issues don't affect LiDAR
3. **Easier Debugging** - Each system can be tested separately
4. **Scalable** - Systems can be deployed on different machines
5. **Maintainable** - Clear separation of concerns

## 🔄 Migration from Combined System

The old combined system (`app.py`) has been replaced with:
- `app_combined.py` - PBT functionality only
- `lidar_monitor.py` - LiDAR functionality only

Both systems maintain the same WebSocket API for backward compatibility.
