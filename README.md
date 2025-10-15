# SICK Capstone - PBT Sensor Web App

A real-time web application for visualizing PBT (Plastic Scintillator with Photomultiplier Tube) sensor waveforms from the SICK capstone project.

## Features

- 📊 Real-time waveform visualization at 800 Hz sample rate
- 📈 Live envelope detection with configurable threshold
- 🔄 WebSocket-based data streaming (20 Hz update rate)
- 📉 Interactive Chart.js graphs with zoom and pan
- 📱 Responsive design for desktop and mobile
- ⏸️ Pause/Resume and Clear controls
- 📊 Live statistics display (baseline, envelope, threshold)

## Architecture

### Backend (Python/Flask)
- **Serial Communication**: Reads ADC data from Arduino at 115200 baud
- **Signal Processing**: Baseline tracking and envelope detection
- **WebSocket Server**: Broadcasts data to connected clients via Flask-SocketIO
- **Threading**: Non-blocking serial reading in background thread

### Frontend (HTML/CSS/JavaScript)
- **Chart.js**: High-performance real-time charting
- **Socket.IO**: WebSocket client for live data updates
- **Responsive UI**: Modern, gradient design with statistics cards

## Prerequisites

### Hardware
- Raspberry Pi (tested on Pi 4)
- Arduino with PBT sensor (or simulator)
- USB connection between Arduino and Raspberry Pi

### Software
- Python 3.7+
- pip package manager

## Installation

### 1. Clone or navigate to the project directory
```bash
cd /Users/adrielrivera/Documents/SICK7/SICK-App
```

### 2. Install Python dependencies
```bash
pip3 install -r requirements.txt
```

### 3. Configure settings
Edit `config.py` to configure the application:
```python
SERIAL_PORT = "/dev/ttyUSB0"  # Change to your Arduino's port
BAUD = 115200                  # Baud rate
HOST = '0.0.0.0'              # Server host
PORT = 5000                   # Server port
```

To find your Arduino's port:
```bash
# On Raspberry Pi/Linux
ls /dev/tty* | grep USB
# or
dmesg | grep tty
```

### 4. Upload Arduino sketch
Upload the `signal_simulator.ino` sketch to your Arduino using the Arduino IDE.

## Usage

### Running the Web App

#### Option 1: Using the Start Script (Recommended)
```bash
./start.sh
```

#### Option 2: Direct Python Execution
```bash
python3 app.py
```

#### Option 3: Test Mode (No Arduino Required)
To test the web interface without connecting the Arduino:
```bash
python3 test_mode.py
```
This will simulate sensor data with realistic waveforms.

### Accessing the Web Interface

1. Open a web browser and navigate to:
```
http://localhost:5000
```

2. Or from another device on the same network:
```
http://<raspberry-pi-ip>:5000
```

### Finding Your Raspberry Pi IP
```bash
hostname -I
```

### Running as a System Service (Optional)

To run the app automatically on boot:

1. Edit `sick-pbt.service` and update paths if needed
2. Install the service:
```bash
sudo cp sick-pbt.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sick-pbt.service
sudo systemctl start sick-pbt.service
```

3. Check status:
```bash
sudo systemctl status sick-pbt.service
```

4. View logs:
```bash
sudo journalctl -u sick-pbt.service -f
```

### Controls

- **Pause/Resume**: Pause the live graph updates (data still received in background)
- **Clear**: Clear all data and reset the graph
- **Connection Status**: Green = connected, Red = disconnected

## Configuration

All configuration settings are centralized in `config.py`. Edit this file to customize the application:

### Serial Communication
```python
SERIAL_PORT = "/dev/ttyUSB0"   # Arduino serial port
BAUD = 115200                  # Baud rate
SAMPLES_PER_SEC = 800         # Expected sample rate
```

### Signal Processing
```python
ENVELOPE_ALPHA = 0.12          # Envelope filter coefficient (0-1, lower = smoother)
TRIGGER_THRESHOLD = 60         # Trigger level for peak detection (ADC counts)
BASELINE_ALPHA = 0.001         # Baseline tracking coefficient (0-1, lower = more stable)
```

### Web Server
```python
HOST = '0.0.0.0'              # Listen on all interfaces
PORT = 5000                   # Web server port
SECRET_KEY = 'your-secret'    # Change for production
DEBUG = False                 # Enable debug mode
```

### Display
```python
BUFFER_SIZE = 4000            # Maximum samples in memory (5 sec at 800 Hz)
EMIT_INTERVAL = 0.05          # Update rate (seconds, 0.05 = 20 Hz)
MAX_DISPLAY_POINTS = 4000     # Maximum points on chart
```

## Troubleshooting

### Serial Port Issues
```bash
# Check if Arduino is connected
ls -l /dev/ttyUSB*

# If permission denied
sudo usermod -a -G dialout $USER
# Then logout and login again
```

### Flask-SocketIO Issues
```bash
# Ensure eventlet or gevent is installed for production
pip3 install eventlet
```

### Port 5000 Already in Use
Edit `app.py` and change the port:
```python
socketio.run(app, host='0.0.0.0', port=8080, debug=False)
```

## Development

### Project Structure
```
SICK-App/
├── app.py                 # Flask backend with WebSocket
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Main HTML template
└── static/
    ├── css/
    │   └── style.css     # Styling
    └── js/
        └── main.js       # Frontend logic and Chart.js
```

### Adding More Sensors

To add additional sensors (e.g., PMT, GM counter):
1. Create new serial reader threads in `app.py`
2. Add new WebSocket event handlers
3. Create new chart canvases in `index.html`
4. Add corresponding JavaScript chart instances in `main.js`

## Performance Notes

- **Sample Rate**: 800 Hz from Arduino
- **Display Update Rate**: 20 Hz (configurable via `emit_interval` in app.py)
- **Buffer Size**: 4000 points (~5 seconds at 800 Hz)
- **Chart Rendering**: Optimized with `animation: false` and `update('none')`

## Future Enhancements

- [ ] Multi-sensor support (PMT, GM counter, etc.)
- [ ] Data logging and export (CSV/JSON)
- [ ] Peak detection and event counting
- [ ] Historical data playback
- [ ] Configurable thresholds via UI
- [ ] Mobile app (React Native)

## License

Capstone Project - SICK Team

## Authors

- SICK Capstone Team
- Adriel Rivera

## Performance & Architecture

**Important:** Running multiple sensors + web server on one Pi can strain resources!

See performance guides:
- **`PERFORMANCE_SUMMARY.md`** - Quick overview of concerns & solutions (start here!)
- **`ARCHITECTURE_CONCERNS.md`** - Detailed technical analysis
- **`monitor_performance.sh`** - Check if your Pi can handle the load
- **`start_optimized.sh`** - Startup script with proper priorities
- **`config_optimized.py`** - Performance-tuned configuration

**TL;DR:** Use Raspberry Pi 4 with 4GB+ RAM, run `./start_optimized.sh`, test under load before demo day!

## Deployment

See deployment guides:
- **`DEPLOYMENT_SUMMARY.md`** - Overview of deployment options (start here!)
- **`DEPLOYMENT.md`** - Complete deployment guide with all methods
- **`DEPLOY_QUICK.md`** - Quick reference card
- **`CONSTANT_URL_GUIDE.md`** - Get a permanent URL for your multi-sensor dashboard
- **`URL_OPTIONS.md`** - Quick URL options summary

**TL;DR:** Since your app needs Arduino access, it must run on the Raspberry Pi. 

**For demos:** Use **ngrok** for instant public access  
**For permanent setup:** Use **Cloudflare Tunnel** (FREE!) with a $1 domain → `sensors.yourdomain.com`

## Acknowledgments

- Arduino community for signal simulation examples
- Flask and Socket.IO documentation
- Chart.js for excellent real-time charting capabilities

