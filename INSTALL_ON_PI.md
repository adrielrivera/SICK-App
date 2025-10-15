# Installation on Raspberry Pi

## Quick Install

Run these commands on your Raspberry Pi:

```bash
cd /path/to/SICK-App

# 1. Install system package for pigpio daemon
sudo apt-get update
sudo apt-get install -y pigpio

# 2. Activate your virtual environment (if you have one)
source venv/bin/activate

# 3. Install Python packages
pip install -r requirements.txt

# 4. Start pigpio daemon
sudo systemctl start pigpiod
sudo systemctl enable pigpiod  # Auto-start on boot

# 5. Make startup script executable
chmod +x start_combined.sh

# 6. Run the app
./start_combined.sh
```

## Step-by-Step Explanation

### 1. Install pigpio System Package

The pigpio library requires both:
- **Python module** (`pip install pigpio`)
- **System daemon** (`pigpiod`)

Install the system package:
```bash
sudo apt-get update
sudo apt-get install -y pigpio
```

This installs the `pigpiod` daemon that controls GPIO pins.

### 2. Install Python Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install all requirements (including pigpio Python module)
pip install -r requirements.txt
```

The `requirements.txt` now includes:
- Flask==3.0.0
- Flask-SocketIO==5.3.5
- python-socketio==5.10.0
- pyserial==3.5
- python-engineio==4.8.0
- **pigpio>=1.78** ← Added!

### 3. Start pigpio Daemon

The daemon must be running for GPIO control:

```bash
# Start now
sudo systemctl start pigpiod

# Enable auto-start on boot
sudo systemctl enable pigpiod

# Check status
sudo systemctl status pigpiod
```

You should see: `Active: active (running)`

### 4. Verify Installation

Test that pigpio works:

```bash
python3 -c "import pigpio; pi = pigpio.pi(); print('pigpio OK!' if pi.connected else 'pigpio FAIL')"
```

Should output: `pigpio OK!`

### 5. Run the App

```bash
./start_combined.sh
```

Or manually:
```bash
source venv/bin/activate
python3 app_combined.py
```

## Troubleshooting

### "No module named pigpio"

**Solution 1**: Install via pip
```bash
source venv/bin/activate
pip install pigpio
```

**Solution 2**: Install system-wide (if venv issues)
```bash
sudo pip3 install pigpio
```

### "pigpio daemon not running"

**Cause**: The `pigpiod` system service isn't installed or started

**Solution**:
```bash
# Install system package
sudo apt-get install pigpio

# Start daemon
sudo systemctl start pigpiod

# Check status
sudo systemctl status pigpiod
```

### "Could not connect to pigpio daemon"

**Solution**: Check if daemon is listening
```bash
# Check if running
ps aux | grep pigpiod

# Try manual start
sudo pigpiod

# Check port 8888 (pigpio uses this)
netstat -tuln | grep 8888
```

### "Permission denied" for GPIO

**Solution**: Run with sudo OR add user to gpio group
```bash
# Option 1: Run with sudo (not recommended for production)
sudo python3 app_combined.py

# Option 2: Add user to gpio group (better)
sudo usermod -a -G gpio $USER
# Logout and login again
```

### Serial Port Permission Denied

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Or temporary fix
sudo chmod 666 /dev/ttyUSB0
```

**Note**: Logout and login after adding to groups!

## Complete Fresh Install Example

Starting from scratch on a clean Raspberry Pi:

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install system packages
sudo apt-get install -y pigpio python3-pip python3-venv

# Navigate to your project
cd /home/pi/SICK-App

# Create virtual environment (if not exists)
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Start pigpio daemon
sudo systemctl start pigpiod
sudo systemctl enable pigpiod

# Add user to necessary groups
sudo usermod -a -G gpio,dialout $USER

# Logout and login (or reboot)
sudo reboot

# After reboot, run the app
cd /home/pi/SICK-App
./start_combined.sh
```

## Verify Everything Works

### 1. Check pigpio daemon
```bash
sudo systemctl status pigpiod
# Should show: Active: active (running)
```

### 2. Check Python module
```bash
source venv/bin/activate
python3 -c "import pigpio; print('OK')"
# Should output: OK
```

### 3. Check serial port
```bash
ls -l /dev/ttyUSB*
# Should show your Arduino device
```

### 4. Check groups
```bash
groups
# Should include: dialout gpio
```

### 5. Run the app
```bash
./start_combined.sh
```

Should see output like:
```
Activating virtual environment...
Starting pigpio daemon...
Starting SICK PBT Combined App...
============================================================
SICK PBT Sensor - Combined Web App + GPIO Pulse Output
============================================================
Serial port: /dev/ttyUSB0 @ 115200 baud
Samples per second: 800
GPIO pulse output: Pin 18
Trigger threshold: 60 ADC counts
Web server: http://0.0.0.0:5000
============================================================
GPIO 18 initialized for pulse output
Baseline calibrated: 42.3 ADC counts
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.100:5000
```

## Access Web Interface

From any device on the same network:
```
http://<raspberry-pi-ip>:5000
```

Example:
```
http://192.168.1.100:5000
```

## Auto-Start on Boot (Optional)

To make the app start automatically when Pi boots:

```bash
# Edit the service file to use app_combined.py
sudo nano /etc/systemd/system/sick-pbt.service
```

Change the ExecStart line to:
```
ExecStart=/home/pi/SICK-App/venv/bin/python /home/pi/SICK-App/app_combined.py
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sick-pbt.service
sudo systemctl start sick-pbt.service
sudo systemctl status sick-pbt.service
```

## Summary Checklist

- [ ] System updated: `sudo apt-get update`
- [ ] pigpio installed: `sudo apt-get install pigpio`
- [ ] Virtual environment activated
- [ ] Python packages installed: `pip install -r requirements.txt`
- [ ] pigpiod daemon running: `sudo systemctl status pigpiod`
- [ ] User in dialout group: `groups | grep dialout`
- [ ] User in gpio group: `groups | grep gpio`
- [ ] Serial port accessible: `ls -l /dev/ttyUSB0`
- [ ] Arduino connected and uploading data
- [ ] App starts without errors
- [ ] Web interface accessible

All good? You're ready to go! 🎉

