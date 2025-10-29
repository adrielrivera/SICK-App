# SICK7 PBT-Only System

## 🎯 **Simplified PBT System (No LiDAR, No Credit Tracking)**

This is a simplified version of the SICK7 PBT system that focuses purely on PBT sensor reading and arcade machine control, without LiDAR monitoring or credit tracking features.

## ✨ **Features**

- **PBT Sensor Reading**: Real-time PBT sensor data processing
- **Peak Detection**: Automatic peak detection and pulse width calculation
- **Arcade Control**: GPIO control via Arduino for arcade machine signaling
- **Web Interface**: Real-time waveform visualization
- **Optimized Scoring**: 30-100 ADC → 40-10ms mapping for better distribution

## 🔧 **Hardware Setup**

### **Arduino Connections:**
- **PBT Sensor** → Pin A0 (Analog input)
- **Arcade Pin 6** → Pin 6 (Digital output) - START signal
- **Arcade Pin 5** → Pin 5 (Digital output) - ACTIVE signal
- **Piezo Buzzer** → Pin 10 (Digital output) - Audio feedback
- **Status LED** → Pin 13 (Digital output) - System status
- **GND** → Common ground

### **Pi Connections:**
- **Arduino** → `/dev/ttyUSB0` or `/dev/ttyACM0` (Serial)

## 🚀 **Setup Instructions**

### **1. Upload Arduino Code:**
```bash
cd ~/SICK-Capstone/SICK-Capstone/arduino_stuff/pbt_only
./upload.sh
```

### **2. Start PBT System:**
```bash
cd ~/SICK7/SICK-App
./start_pbt_only.sh
```

### **3. Access Web Interface:**
- Open browser to `http://localhost:5000`
- View real-time PBT waveform and statistics

## 📊 **System Behavior**

### **PBT Processing:**
1. **Sensor Reading**: 800Hz sampling rate from Arduino
2. **Peak Detection**: Triggers on envelope > threshold
3. **Pulse Calculation**: Maps peak to pulse width (30-100 ADC → 40-10ms)
4. **Arcade Signaling**: Sends GPIO commands to Arduino

### **Arcade Control Sequence:**
1. **Pin 6 HIGH** → Start signal to arcade
2. **Wait** → Calculated pulse width duration
3. **Pin 5 LOW** → Active signal to arcade
4. **Reset** → Both pins return to idle state

### **Expected Scoring:**
- **30 ADC** → 40.0ms pulse → ~380 points
- **50 ADC** → 31.4ms pulse → ~410 points
- **70 ADC** → 22.9ms pulse → ~440 points
- **90 ADC** → 14.3ms pulse → ~478 points
- **100 ADC** → 10.0ms pulse → ~500 points

## 📁 **Files**

### **Pi Code:**
- **`app_pbt_only.py`** - Main PBT application
- **`start_pbt_only.sh`** - Startup script
- **`config.py`** - Configuration settings

### **Arduino Code:**
- **`pbt_only.ino`** - Arduino sketch for PBT sensor + GPIO
- **`upload.sh`** - Arduino upload script

## 🎮 **Usage**

1. **Connect Hardware**: PBT sensor to Arduino, Arduino to Pi
2. **Upload Arduino Code**: Run `upload.sh` in Arduino directory
3. **Start Pi System**: Run `./start_pbt_only.sh`
4. **Test PBT**: Hit the PBT sensor and watch the web interface
5. **Check Arcade**: Verify arcade machine receives signals

## 🔍 **Troubleshooting**

### **Arduino Not Detected:**
- Check USB connection
- Try different port (`/dev/ttyUSB0` vs `/dev/ttyACM0`)
- Check Arduino IDE for port detection

### **No PBT Data:**
- Verify PBT sensor connection to Pin A0
- Check Arduino serial output
- Ensure Pi can read from Arduino port

### **Arcade Not Responding:**
- Check GPIO connections (Pin 6 and Pin 5)
- Verify arcade machine is powered on
- Check Arduino serial output for GPIO commands

## 📈 **Performance**

- **Sampling Rate**: 800Hz (same as original system)
- **Latency**: <1ms from peak detection to arcade signal
- **Memory**: Efficient circular buffer for waveform data
- **Reliability**: Simplified code, fewer failure points

## 🎯 **Advantages of PBT-Only System**

1. **Simpler**: No complex LiDAR or credit tracking
2. **More Reliable**: Fewer components to fail
3. **Easier Debugging**: Clear data flow
4. **Better Performance**: No overhead from safety systems
5. **Focused**: Pure PBT sensor functionality

**This system is perfect for PBT testing and development without the complexity of safety monitoring!** 🚀
