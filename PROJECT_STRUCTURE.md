# SICK PBT Sensor Web App - Project Structure

## Overview
This web application provides real-time visualization of PBT (Plastic Scintillator with Photomultiplier Tube) sensor data from an Arduino connected to a Raspberry Pi.

## File Structure

```
SICK-App/
├── app.py                      # Main Flask application with WebSocket
├── config.py                   # Centralized configuration settings
├── test_mode.py               # Test mode with simulated data
├── requirements.txt           # Python dependencies
├── start.sh                   # Convenience startup script
├── sick-pbt.service          # SystemD service file
├── signal_simulator.ino      # Arduino signal simulator sketch
├── pbt_pulse_plot.py         # Original matplotlib plotting script
├── README.md                 # Main documentation
├── PROJECT_STRUCTURE.md      # This file
├── .gitignore               # Git ignore rules
│
├── templates/
│   └── index.html           # Main web interface template
│
└── static/
    ├── css/
    │   └── style.css        # Application styling
    └── js/
        └── main.js          # Frontend logic and charting
```

## Application Flow

### Data Flow Diagram
```
Arduino (signal_simulator.ino)
    ↓ [Serial: 115200 baud, ~800 Hz]
Raspberry Pi (app.py)
    ├─→ Serial Reader Thread
    │   ├─→ Baseline Tracking
    │   └─→ Envelope Detection
    ↓ [WebSocket: ~20 Hz batches]
Web Browser (index.html + main.js)
    └─→ Chart.js Real-time Visualization
```

## Component Details

### Backend (Python/Flask)

#### `app.py` - Main Application
- **Serial Communication**: Reads ADC data from Arduino
- **Signal Processing**: 
  - Baseline tracking (exponential moving average)
  - Envelope detection for peak finding
- **WebSocket Server**: Broadcasts data to connected clients
- **Threading**: Non-blocking serial reading

#### `config.py` - Configuration
- Serial port settings
- Signal processing parameters
- Web server configuration
- Display settings

#### `test_mode.py` - Simulator
- Runs without Arduino
- Generates realistic waveforms
- Useful for development and testing

### Frontend (HTML/CSS/JavaScript)

#### `templates/index.html`
- Main web interface
- Statistics dashboard
- Chart container
- System information panel

#### `static/css/style.css`
- Modern gradient design
- Responsive layout
- Card-based UI components
- Mobile-friendly

#### `static/js/main.js`
- WebSocket client (Socket.IO)
- Chart.js integration
- Real-time data buffering
- Interactive controls

### Hardware Integration

#### `signal_simulator.ino` - Arduino
- Generates test signals at 800 Hz
- Simulates quiet baseline with noise
- Occasional hits with half-sine envelope
- Configurable peak amplitudes and durations

## Key Features

### 1. Real-time Data Streaming
- **Sample Rate**: 800 Hz from Arduino
- **Update Rate**: 20 Hz to browser (configurable)
- **Buffer Size**: 4000 points (~5 seconds)

### 2. Signal Processing
- **Baseline Tracking**: Adaptive baseline using exponential moving average
- **Envelope Detection**: Peak finding with configurable threshold
- **Noise Handling**: Robust to baseline drift

### 3. Web Interface
- **Live Charts**: High-performance Chart.js visualization
- **Statistics**: Real-time baseline, envelope, and threshold display
- **Controls**: Pause/Resume and Clear functionality
- **Responsive**: Works on desktop and mobile

### 4. Configuration
- Centralized settings in `config.py`
- Easy serial port configuration
- Adjustable signal processing parameters
- Customizable display options

## Technology Stack

### Backend
- **Python 3.7+**: Core language
- **Flask 3.0**: Web framework
- **Flask-SocketIO 5.3**: WebSocket support
- **pySerial 3.5**: Serial communication

### Frontend
- **Chart.js 4.4**: Real-time charting
- **Socket.IO 4.5**: WebSocket client
- **Vanilla JavaScript**: No framework dependencies
- **Modern CSS**: Flexbox and Grid layouts

### Hardware
- **Raspberry Pi**: Server host
- **Arduino**: Sensor interface
- **USB Serial**: Communication link

## Development Workflow

### 1. Testing Without Hardware
```bash
python3 test_mode.py
```
Uses simulated data - no Arduino required

### 2. Development Mode
```bash
# Edit config.py to enable debug mode
DEBUG = True

# Run application
python3 app.py
```

### 3. Production Deployment
```bash
# Edit config.py for production
DEBUG = False
SECRET_KEY = 'secure-random-key'

# Install as system service
sudo cp sick-pbt.service /etc/systemd/system/
sudo systemctl enable sick-pbt.service
sudo systemctl start sick-pbt.service
```

## Signal Processing Pipeline

### 1. Data Acquisition
```python
# Read from serial port
value = read_one_int(ser)  # 0-1023 ADC counts
```

### 2. Baseline Tracking
```python
# Exponential moving average
baseline = (1 - BASELINE_ALPHA) * baseline + BASELINE_ALPHA * value
```

### 3. Envelope Detection
```python
# Magnitude from baseline
xmag = abs(value - baseline)

# Envelope tracking
envelope = (1 - ENVELOPE_ALPHA) * envelope + ENVELOPE_ALPHA * xmag
```

### 4. Peak Detection
```python
# Trigger when envelope exceeds threshold
if envelope > TRIGGER_THRESHOLD:
    # Record peak event
    peak_detected = True
```

## Performance Considerations

### Optimizations
1. **Batched Updates**: Send data in 50ms batches instead of individual samples
2. **Chart Performance**: Disabled animations, use update('none') mode
3. **Buffer Management**: Fixed-size deques prevent memory growth
4. **Threading**: Non-blocking serial reading in separate thread

### Scalability
- **Current**: Single sensor, 800 Hz, 20 Hz updates
- **Future**: Multi-sensor support with separate threads
- **Network**: Multiple clients supported via WebSocket broadcast

## Extension Points

### Adding New Sensors
1. Create new serial reader thread in `app.py`
2. Add WebSocket events for new sensor data
3. Create new chart in `index.html`
4. Add corresponding JavaScript chart in `main.js`

### Data Logging
```python
# Add to serial_reader_thread()
with open('data.csv', 'a') as f:
    f.write(f"{timestamp},{value},{baseline},{envelope}\n")
```

### Advanced Analysis
- FFT frequency analysis
- Peak counting and statistics
- Event correlation between sensors
- Historical data playback

## Troubleshooting Guide

### Common Issues

1. **Serial Port Not Found**
   - Check USB connection
   - Verify port name: `ls /dev/tty*`
   - Update `config.py`

2. **Permission Denied**
   - Add user to dialout group: `sudo usermod -a -G dialout $USER`
   - Logout and login again

3. **Chart Not Updating**
   - Check browser console for errors
   - Verify WebSocket connection status
   - Check network/firewall settings

4. **High CPU Usage**
   - Reduce `EMIT_INTERVAL` in config
   - Decrease `MAX_DISPLAY_POINTS`
   - Check for runaway threads

## Future Enhancements

### Planned Features
- [ ] Multi-sensor dashboard (PMT, GM counter, etc.)
- [ ] Data export (CSV, JSON, HDF5)
- [ ] Peak detection and event counting
- [ ] Historical data playback
- [ ] Configurable thresholds via UI
- [ ] Mobile app (React Native)
- [ ] Advanced signal analysis (FFT, statistics)
- [ ] Alert system for threshold violations
- [ ] Cloud data logging

### Architecture Improvements
- [ ] Database integration (PostgreSQL, InfluxDB)
- [ ] REST API for historical data
- [ ] User authentication
- [ ] Multi-user support with separate sessions
- [ ] Docker containerization
- [ ] Kubernetes deployment

## License & Credits

**Project**: SICK Capstone  
**Author**: Adriel Rivera  
**Framework**: Flask + Socket.IO + Chart.js  
**Hardware**: Arduino + Raspberry Pi  

## Support

For issues or questions:
1. Check README.md for setup instructions
2. Review this document for architecture details
3. Check GitHub issues (if applicable)
4. Contact the development team

