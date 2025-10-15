# Serial Port Conflict - FIXED ✅

## The Problem

You were running two scripts simultaneously:
1. `app.py` - Web visualization server
2. `pbt_pulse_plot.py` - GPIO pulse generator with matplotlib

**Both tried to access `/dev/ttyUSB0` at the same time** → Serial port conflict error!

## The Solution

Created `app_combined.py` that merges both scripts into one unified application.

## What Changed

### ✅ Single Serial Connection
- Only ONE script reads from the Arduino
- No more port conflicts

### ✅ Web Interface + GPIO Pulses
- Web-based visualization (better than matplotlib)
- GPIO pulse generation based on peaks
- Pulse counter displayed in web UI
- All statistics in real-time

### ✅ Easy to Run
```bash
# On your Raspberry Pi:
cd /path/to/SICK-App
./start_combined.sh
```

Or manually:
```bash
sudo systemctl start pigpiod  # Start GPIO daemon
source venv/bin/activate      # Activate Python environment
python3 app_combined.py       # Run combined app
```

## How to Use

1. **Upload Arduino sketch** to your Arduino
   - File: `signal_simulator.ino`

2. **Connect Arduino** to Raspberry Pi via USB
   - Should appear as `/dev/ttyUSB0`

3. **Start the combined app**:
   ```bash
   ./start_combined.sh
   ```

4. **Open web browser** on any device:
   - URL: `http://<raspberry-pi-ip>:5000`
   - Example: `http://192.168.1.100:5000`

5. **Monitor**:
   - Web UI shows live waveforms, stats, and pulse count
   - Console shows pulse events: `Pulse #5: Peak=324.7 → 820 ms`
   - GPIO Pin 18 outputs pulses based on detected peaks

## Files Created/Modified

### New Files:
- ✨ `app_combined.py` - **Main combined application**
- ✨ `start_combined.sh` - Startup script
- ✨ `COMBINED_APP_README.md` - Detailed documentation
- ✨ `QUICK_FIX_SUMMARY.md` - This file

### Modified Files:
- 📝 `templates/index.html` - Added pulse count display
- 📝 `static/js/main.js` - Added pulse count updates

### Old Files (Keep for Reference):
- 📄 `app.py` - Original web app (no GPIO)
- 📄 `pbt_pulse_plot.py` - Original GPIO script (no web)

## Configuration

All settings in `config.py`:

```python
SERIAL_PORT = "/dev/ttyUSB0"     # Arduino port
BAUD = 115200                     # Baud rate
TRIGGER_THRESHOLD = 60            # Detection threshold
HOST = '0.0.0.0'                  # Web server host
PORT = 5000                       # Web server port
```

GPIO pin set in `app_combined.py`:
```python
GPIO_PULSE = 18  # BCM pin numbering
```

## Architecture Diagram

```
┌─────────────┐
│   Arduino   │ (Sends ADC samples via serial)
│   Sensor    │
└──────┬──────┘
       │ USB (/dev/ttyUSB0)
       ↓
┌──────────────────────────┐
│  app_combined.py         │
│  ┌────────────────────┐  │
│  │ Serial Reader      │  │ Single thread reads data
│  │ - Baseline track   │  │
│  │ - Envelope detect  │  │
│  └────────┬───────────┘  │
│           ↓              │
│  ┌────────────────────┐  │
│  │ Peak Detection     │  │ Trigger logic
│  │ - Armed/Triggered  │  │
│  │ - Amplitude map    │  │
│  └────────┬───────────┘  │
│           ↓              │
│  ┌────────────────────┐  │
│  │ GPIO Output        │──┼─→ GPIO Pin 18
│  │ (pigpio)           │  │   (Pulse width: 60-1500ms)
│  └────────────────────┘  │
│           ↓              │
│  ┌────────────────────┐  │
│  │ Flask/SocketIO     │  │
│  │ Web Server         │  │
│  └────────┬───────────┘  │
└───────────┼──────────────┘
            ↓
       Port 5000
            ↓
    ┌───────────────┐
    │  Web Browser  │ (Chart.js visualization)
    │  - Real-time  │
    │  - Any device │
    └───────────────┘
```

## Benefits

| Feature | Before | After |
|---------|--------|-------|
| Serial Port | ❌ Conflict | ✅ Single access |
| Web UI | ✅ Yes | ✅ Yes (enhanced) |
| GPIO Pulses | ✅ Yes | ✅ Yes |
| Pulse Counter | ❌ No | ✅ Yes (web + console) |
| Matplotlib | ✅ Yes | ❌ No (web is better) |
| Ease of Use | ❌ Run 2 scripts | ✅ Run 1 script |
| Monitoring | ❌ Separate windows | ✅ Unified interface |

## Testing Checklist

- [ ] Arduino connected and recognized: `ls /dev/ttyUSB*`
- [ ] pigpio daemon running: `sudo systemctl status pigpiod`
- [ ] Virtual environment activated
- [ ] App starts without errors
- [ ] Web interface loads at `http://localhost:5000`
- [ ] Waveforms updating in real-time
- [ ] Baseline shows reasonable value (~40 ADC)
- [ ] Pulses detected and counted
- [ ] GPIO pin outputs pulses (check with LED/oscilloscope)
- [ ] No serial port errors

## Troubleshooting

### "Could not open serial port"
```bash
# Check device exists
ls -l /dev/ttyUSB*

# Add user to dialout group (logout/reboot after)
sudo usermod -a -G dialout $USER

# Check permissions
sudo chmod 666 /dev/ttyUSB0  # Temporary fix
```

### "pigpio daemon not running"
```bash
# Start daemon
sudo systemctl start pigpiod

# Enable auto-start
sudo systemctl enable pigpiod

# Check status
sudo systemctl status pigpiod
```

### No pulses detected
- Lower `TRIGGER_THRESHOLD` in `config.py`
- Check Arduino is sending data (should see values in console)
- Verify sensor is working
- Check waveform in web UI

### Web interface not loading
- Check firewall: `sudo ufw status`
- Allow port: `sudo ufw allow 5000`
- Try different browser
- Check Flask is running: `ps aux | grep app_combined`

## Next Steps

1. **Deploy to your Raspberry Pi**
   - Copy the `SICK-App` folder
   - Install dependencies if needed: `pip install -r requirements.txt`

2. **Test the combined app**
   - Run `./start_combined.sh`
   - Check web interface
   - Verify GPIO output

3. **Auto-start on boot** (optional)
   ```bash
   # Copy service file
   sudo cp sick-pbt.service /etc/systemd/system/
   
   # Edit to use app_combined.py instead of app.py
   sudo nano /etc/systemd/system/sick-pbt.service
   
   # Enable service
   sudo systemctl enable sick-pbt.service
   sudo systemctl start sick-pbt.service
   ```

## Questions?

Read the detailed documentation in `COMBINED_APP_README.md`

Happy sensing! 🎯

