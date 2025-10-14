# SICK PBT Sensor - Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Dependencies
```bash
pip3 install -r requirements.txt
```

### Step 2: Configure Serial Port
Edit `config.py`:
```python
SERIAL_PORT = "/dev/ttyUSB0"  # Change to your Arduino port
```

### Step 3: Run the App
```bash
./start.sh
```

### Step 4: Open Browser
Navigate to: **http://localhost:5000**

---

## 🧪 Test Without Arduino

No hardware? No problem! Run in test mode:
```bash
python3 test_mode.py
```

This simulates realistic sensor data for testing the web interface.

---

## 📋 Common Tasks

### Find Arduino Serial Port
```bash
ls /dev/tty* | grep USB
```

### Check If App Is Running
```bash
ps aux | grep app.py
```

### Stop the App
Press `Ctrl+C` in the terminal

### Change Port Number
Edit `config.py`:
```python
PORT = 8080  # Change from 5000 to 8080
```

### View Real-time Logs
```bash
tail -f /var/log/sick-pbt.log  # If running as service
```

---

## 🔧 Adjusting Signal Processing

All in `config.py`:

### Reduce Noise (Smoother Signal)
```python
ENVELOPE_ALPHA = 0.05  # Lower = smoother (default: 0.12)
```

### Change Trigger Sensitivity
```python
TRIGGER_THRESHOLD = 80  # Higher = less sensitive (default: 60)
```

### Faster Baseline Adaptation
```python
BASELINE_ALPHA = 0.01  # Higher = faster adaptation (default: 0.001)
```

---

## 🌐 Access from Other Devices

### 1. Find Your Raspberry Pi's IP
```bash
hostname -I
```

### 2. Access from Phone/Tablet/Computer
```
http://<raspberry-pi-ip>:5000
```
Example: `http://192.168.1.100:5000`

---

## 🛠️ Troubleshooting

### Problem: "Permission denied" on serial port
**Solution:**
```bash
sudo usermod -a -G dialout $USER
# Then logout and login
```

### Problem: Port 5000 already in use
**Solution:** Change port in `config.py`:
```python
PORT = 8080
```

### Problem: Chart not updating
**Solutions:**
1. Check browser console (F12) for errors
2. Verify connection status (should be green)
3. Refresh page (Ctrl+R)

### Problem: Arduino not detected
**Solutions:**
1. Check USB cable connection
2. Verify Arduino is powered on
3. Check serial port with `ls /dev/tty*`
4. Try different USB port

---

## 📊 Understanding the Display

### Raw Signal (Blue Line)
- Shows actual ADC values (0-1023)
- Includes baseline noise and hits

### Envelope (Red Line)
- Processed signal showing detected peaks
- Used for trigger threshold comparison

### Threshold (Orange Dashed Line)
- Trigger level for peak detection
- Adjust in `config.py` as `TRIGGER_THRESHOLD`

### Statistics Panel
- **Baseline**: Current noise floor level
- **Current Envelope**: Real-time envelope value
- **Threshold**: Configured trigger level
- **Connection**: WebSocket status

---

## 🎯 Performance Tips

### For Slower Raspberry Pi Models
```python
# In config.py
EMIT_INTERVAL = 0.1      # Update less frequently (10 Hz)
BUFFER_SIZE = 2000       # Smaller buffer
MAX_DISPLAY_POINTS = 2000
```

### For Faster Updates
```python
# In config.py
EMIT_INTERVAL = 0.025    # Update more frequently (40 Hz)
```

### Reduce Browser CPU Usage
1. Click "Pause" to stop chart updates
2. Reduce browser zoom level
3. Close other browser tabs

---

## 🔄 Running as Background Service

### Install Service
```bash
sudo cp sick-pbt.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sick-pbt.service
sudo systemctl start sick-pbt.service
```

### Useful Commands
```bash
# Check status
sudo systemctl status sick-pbt.service

# View logs
sudo journalctl -u sick-pbt.service -f

# Restart service
sudo systemctl restart sick-pbt.service

# Stop service
sudo systemctl stop sick-pbt.service

# Disable auto-start
sudo systemctl disable sick-pbt.service
```

---

## 📱 Controls

| Button | Action |
|--------|--------|
| **Pause** | Pause chart updates (data still received) |
| **Resume** | Resume chart updates |
| **Clear** | Clear all data and reset chart |

---

## 🔍 Keyboard Shortcuts (in browser)

- `F12` - Open developer console
- `Ctrl+R` - Refresh page
- `Ctrl+Shift+R` - Hard refresh (clear cache)
- `Ctrl+Plus` - Zoom in
- `Ctrl+Minus` - Zoom out

---

## 📈 What's Normal?

### Typical Values
- **Baseline**: 30-50 ADC counts
- **Noise**: ±5-10 counts around baseline
- **Hit Peaks**: 200-900 ADC counts
- **Hit Duration**: 120-320 ms

### Warning Signs
- Baseline > 100: Check sensor or noise sources
- No peaks: Check Arduino connection
- Constant high values: Check sensor/Arduino

---

## 🎓 Next Steps

1. ✅ Get basic visualization working
2. 📊 Tune signal processing parameters
3. 🔬 Connect real PBT sensor
4. 📱 Access from mobile devices
5. 🌐 Set up as permanent service
6. 📈 Add additional sensors (PMT, GM counter)
7. 💾 Implement data logging

---

## 📚 Additional Resources

- **Full Documentation**: See `README.md`
- **Architecture Details**: See `PROJECT_STRUCTURE.md`
- **Configuration Reference**: See `config.py`
- **Original Script**: See `pbt_pulse_plot.py`

---

## 💡 Tips

### Calibration
Run for 30 seconds to let baseline stabilize after startup

### Best Browser
Chrome/Chromium recommended for best Chart.js performance

### Network Performance
Use wired Ethernet on Raspberry Pi for best stability

### Development
Set `DEBUG = True` in `config.py` for detailed Flask logging

---

## 🐛 Getting Help

1. Check browser console (F12) for JavaScript errors
2. Check terminal for Python errors
3. Verify serial connection with test mode first
4. Review configuration in `config.py`
5. See `README.md` troubleshooting section

---

**Happy Sensing! 📊✨**

