# PBT Simulator - Custom Peak Only

## 🎯 **Changes Made**

All random peak generation features have been removed. The system now only supports **custom peak input**.

## 🔧 **What Was Removed**

### **Arduino Simulator:**
- ❌ Random peak generation arrays and probabilities
- ❌ `generateRandomPeak()` function
- ❌ `GENERATE_PEAK` command handler
- ❌ Random peak timing variables
- ❌ Automatic peak generation in main loop

### **Pi Tester:**
- ❌ `generate_peak` WebSocket handler
- ❌ Random peak command sending

### **Web Interface:**
- ❌ "Generate Random Peak" button
- ❌ Random peak event listener

## ✅ **What Remains**

### **Arduino Simulator:**
- ✅ Custom peak input (`CUSTOM_PEAK:amplitude`)
- ✅ Waveform generation on Pin 3
- ✅ Arcade signal control (Pins 6 & 5)
- ✅ LiDAR monitoring (Pins 8 & 9)
- ✅ Serial communication

### **Pi Tester:**
- ✅ Custom peak WebSocket handler
- ✅ Waveform processing algorithm
- ✅ Arcade signal generation
- ✅ Real-time data streaming

### **Web Interface:**
- ✅ Custom peak input field
- ✅ "Generate Custom Peak" button
- ✅ Real-time waveform display
- ✅ Simulation controls (start/stop)

## 🎮 **How to Use**

### **1. Upload Arduino Simulator:**
```bash
cd ~/SICK/SICK-App
arduino-cli compile --fqbn arduino:avr:uno SICK-App.ino
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno SICK-App.ino
```

### **2. Start Pi Tester:**
```bash
./start_tester.sh
```

### **3. Open Web Interface:**
```
http://localhost:5002
```

### **4. Generate Custom Peaks:**
1. Click "Start Simulation"
2. Enter desired amplitude (0-200 ADC)
3. Click "Generate Custom Peak"
4. Watch oscilloscope Pin 3 for the exact peak

## 📊 **Available Commands**

### **Arduino Commands:**
- `CUSTOM_PEAK:45` - Generate peak with 45 ADC amplitude
- `START_SIMULATION` - Start waveform generation
- `STOP_SIMULATION` - Stop waveform generation
- `PIN6_HIGH/LOW` - Control arcade start signal
- `PIN5_HIGH/LOW` - Control arcade active signal

### **Web Interface:**
- **Start Simulation** - Begin waveform generation
- **Stop Simulation** - Pause waveform generation
- **Generate Custom Peak** - Create peak with specified amplitude
- **Refresh** - Update waveform display

## 🎯 **Benefits of Custom Peak Only**

1. **Precise Control** - Exact peak amplitudes every time
2. **Reproducible Testing** - Same results for same inputs
3. **Cleaner Interface** - No confusing random elements
4. **Better Debugging** - Predictable behavior
5. **Educational** - Learn exact peak-to-pulse relationships

## 🔍 **Expected Behavior**

### **When Simulation Started:**
- Pin 3 outputs baseline waveform (~2.5V)
- Small random noise around baseline
- No automatic peaks

### **When Custom Peak Generated:**
- Pin 3 outputs exact amplitude spike
- Bell-curve shape (smooth rise and fall)
- Duration: ~50ms
- Pi processes peak and sends arcade signal

### **Oscilloscope Readings:**
- **Channel 1 (Pin 3)**: Custom peak waveforms
- **Channel 2 (Pin 6)**: Arcade start signals
- **Channel 3 (Pin 5)**: Arcade active signals

**The system now provides complete control over peak generation for precise testing!** 🎯
