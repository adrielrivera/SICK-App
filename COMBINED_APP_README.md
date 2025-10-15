# SICK PBT Sensor - Combined Application

## Problem Solved

Previously, you had **two separate scripts** trying to access the same serial port:
- `app.py` - Web visualization
- `pbt_pulse_plot.py` - GPIO pulse generation with matplotlib

**This caused a serial port conflict** because only one process can access a serial port at a time.

## Solution

`app_combined.py` combines both functionalities into a **single script** that:
- ✅ Reads serial data from Arduino **once**
- ✅ Provides web-based real-time visualization (Flask + SocketIO + Chart.js)
- ✅ Generates GPIO pulses based on detected peaks (pigpio)
- ✅ Shows pulse count in web interface
- ✅ No serial port conflicts!

## Features

### Web Interface
- Real-time waveform visualization (raw signal + envelope)
- Live statistics (baseline, envelope, threshold, pulse count)
- Responsive Chart.js graphs
- Pause/Resume and Clear controls
- Connection status indicator
- Accessible from any device on the network

### GPIO Pulse Output
- Automatic peak detection with trigger threshold
- Maps peak amplitude to pulse width (60-1500 ms)
- Refractory period to prevent double-triggering
- Re-arm logic for clean detection
- Console output showing pulse details

## Requirements

1. **pigpio daemon** (for GPIO control)
   ```bash
   sudo systemctl start pigpiod
   sudo systemctl enable pigpiod  # Auto-start on boot
   ```

2. **Python packages** (already in venv)
   - flask
   - flask-socketio
   - pyserial
   - pigpio

## Usage

### Quick Start
```bash
cd /home/pi/SICK-App  # Or wherever your app is
./start_combined.sh
```

### Manual Start
```bash
# Start pigpio daemon
sudo systemctl start pigpiod

# Activate virtual environment
source venv/bin/activate

# Run combined app
python3 app_combined.py
```

### Access Web Interface
Open a browser and navigate to:
- From Pi itself: `http://localhost:5000`
- From another device: `http://<raspberry-pi-ip>:5000`

Example: `http://192.168.1.100:5000`

## Configuration

Edit `config.py` to adjust:

```python
# Serial port settings
SERIAL_PORT = "/dev/ttyUSB0"
BAUD = 115200

# Signal processing
TRIGGER_THRESHOLD = 60      # Detection threshold
ENVELOPE_ALPHA = 0.12       # Envelope smoothing
BASELINE_ALPHA = 0.001      # Baseline tracking

# Web server
HOST = '0.0.0.0'            # Listen on all interfaces
PORT = 5000                 # Web server port
```

## GPIO Pin Configuration

Default GPIO pin: **18** (BCM numbering)

To change, edit `app_combined.py`:
```python
GPIO_PULSE = 18  # Change to your desired GPIO pin
```

## Monitoring

### Console Output
The app shows:
- Baseline calibration value
- Sample rate (SPS)
- Pulse events: `Pulse #1: Peak=245.3 → 480 ms`
- Client connections/disconnections

### Web Interface
- **Baseline**: Tracked DC offset
- **Current Envelope**: Real-time envelope value
- **Threshold**: Trigger level
- **Pulse Count**: Total pulses fired
- **Sample Count**: Total samples received
- **Buffer Size**: Current buffer length

## Stopping the App

Press `Ctrl+C` to stop gracefully. The app will:
- Close serial connection
- Turn off GPIO output
- Stop pigpio connection
- Shut down web server

## Troubleshooting

### Serial Port Error
```
ERROR: Could not open serial port /dev/ttyUSB0
```
**Solution**: 
- Check Arduino is connected: `ls /dev/ttyUSB*`
- Add user to dialout group: `sudo usermod -a -G dialout $USER`
- Restart Pi after adding to group

### GPIO Not Working
```
WARNING: pigpio daemon not running. GPIO pulses disabled.
```
**Solution**:
```bash
sudo systemctl start pigpiod
sudo systemctl status pigpiod
```

### Port Already in Use
```
Address already in use
```
**Solution**:
- Another app is using port 5000
- Kill the other process or change PORT in `config.py`

### No Pulses Being Generated
- Check threshold: Lower `TRIGGER_THRESHOLD` in `config.py`
- Check GPIO connection with multimeter/oscilloscope
- Monitor console for "Pulse #" messages

## Architecture

```
Arduino (Serial) → app_combined.py → Flask/SocketIO → Web Browser
                                   ↘ pigpio → GPIO Pin 18
```

**Single thread** reads serial data and:
1. Processes envelope detection
2. Detects peaks and generates GPIO pulses
3. Buffers data for web clients
4. Emits updates via WebSocket

## Comparison with Old Setup

| Feature | Old Setup | Combined App |
|---------|-----------|--------------|
| Serial Access | ⚠️ Conflict | ✅ Single reader |
| Web Interface | ✅ Yes | ✅ Enhanced |
| GPIO Pulses | ✅ Yes | ✅ Yes |
| Matplotlib Plot | ✅ Yes | ❌ No (better web UI) |
| Easy to Use | ❌ Two scripts | ✅ One script |
| Pulse Count Display | ❌ Console only | ✅ Web + Console |

## Future Enhancements

Possible additions:
- [ ] Adjustable threshold via web UI
- [ ] Data logging to CSV
- [ ] Historical pulse statistics
- [ ] Multiple GPIO outputs
- [ ] Audio feedback for pulses
- [ ] Mobile-optimized UI

## License

Part of SICK Capstone Project

