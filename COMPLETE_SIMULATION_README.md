# SICK7 Complete PBT Simulation System

## 🎯 Overview

This system provides a **complete PBT simulation** that generates realistic waveforms, processes them through the same algorithm as the real system, and sends actual arcade signals. Perfect for testing, debugging, and demonstration without physical PBT hardware.

## 🔧 System Components

### **1. Arduino Simulator (`arduino_pbt_simulator.ino`)**
- **Generates realistic PBT waveforms** on Pin 3 (PWM)
- **Simulates random peaks** with different amplitudes
- **Outputs to oscilloscope** for verification
- **Responds to Pi commands** for control

### **2. Pi Tester (`pbt_tester.py`)**
- **Reads simulated waveforms** from Arduino
- **Processes through real algorithm** (same as production)
- **Sends arcade signals** via GPIO
- **Web interface** with real-time waveform display

### **3. Web Interface (`pbt_tester.html`)**
- **Real-time waveform display** with canvas
- **Simulation controls** (start/stop/generate peaks)
- **Live data** (samples, pulses, armed status)
- **Oscilloscope-style visualization**

## 🚀 Quick Start

### **Step 1: Upload Arduino Simulator**
```bash
./start_arduino_simulator.sh
```

### **Step 2: Start Pi Tester**
```bash
./start_tester.sh
```

### **Step 3: Open Web Interface**
```
http://localhost:5002
```

### **Step 4: Connect Oscilloscope**
- **Pin 3** → Channel 1 (PBT Waveform)
- **Pin 6** → Channel 2 (Arcade Start)
- **Pin 5** → Channel 3 (Arcade Active)
- **GND** → Ground

## 📊 What You'll See

### **Arduino Output (Pin 3)**
- **Baseline**: ~2.5V (512 ADC = 128 PWM)
- **Noise**: ±0.1V random variation
- **Peaks**: 0.5V to 2.5V spikes (30-100 ADC)
- **Frequency**: 800Hz sampling rate

### **Web Interface**
- **Real-time waveform** with grid and labels
- **Envelope tracking** (red line)
- **Baseline** (green line)
- **Threshold** (yellow dashed line)
- **Live statistics** (samples, pulses, armed status)

### **Oscilloscope**
- **Channel 1**: PBT waveform (Pin 3)
- **Channel 2**: Arcade start signal (Pin 6)
- **Channel 3**: Arcade active signal (Pin 5)

## 🎮 Controls

### **Web Interface Buttons**
- **Start Simulation**: Begin waveform generation
- **Stop Simulation**: Pause waveform generation
- **Generate Peak**: Create random peak immediately
- **Refresh**: Update waveform display

### **Arduino Commands (via Serial)**
- `START_SIMULATION`: Start waveform generation
- `STOP_SIMULATION`: Stop waveform generation
- `GENERATE_PEAK`: Generate random peak
- `STATUS`: Get current status

## 🔬 Technical Details

### **Waveform Generation**
```cpp
// Arduino generates realistic PBT-like waveform
- Baseline around 512 ADC (2.5V)
- Random noise ±5 ADC
- Bell-curve peaks with varying amplitudes
- 800Hz sampling rate
```

### **Peak Detection Algorithm**
```python
# Same algorithm as production system
- Baseline tracking (0.001 alpha)
- Envelope detection (0.12 alpha)
- Trigger threshold: 24 ADC
- Capture window: 250ms
- Inverse mapping: high peak → short pulse
```

### **Arcade Signal Generation**
```python
# Real GPIO control
Pin 6 HIGH → Wait duration → Pin 5 LOW → Reset
- Pin 6: Press START signal
- Pin 5: Press ACTIVE signal
- Duration: 10-100ms based on peak amplitude
```

## 📈 Peak Types and Scoring

### **Random Peak Generation**
- **Low Peaks** (30 ADC): 70% probability → Long pulse (80-100ms)
- **Medium Peaks** (60 ADC): 25% probability → Medium pulse (40-80ms)
- **High Peaks** (100 ADC): 5% probability → Short pulse (10-40ms)

### **Scoring System**
- **HIGH SCORE**: Peak > 50 → Pulse < 20ms
- **MEDIUM SCORE**: Peak 30-50 → Pulse 20-50ms
- **LOW SCORE**: Peak 24-30 → Pulse > 50ms
- **NO SCORE**: Peak < 24 (No trigger)

## 🔍 Debugging Features

### **Real-time Monitoring**
- **Sample count**: Total samples processed
- **Pulse count**: Number of detected peaks
- **Armed status**: Whether system is ready to detect
- **Baseline value**: Current baseline level
- **Envelope value**: Current envelope level

### **Oscilloscope Verification**
- **Pin 3**: Verify waveform generation
- **Pin 6**: Verify arcade start signals
- **Pin 5**: Verify arcade active signals
- **Timing**: Verify pulse durations

## 🎯 Use Cases

### **1. System Testing**
- Test PBT algorithm without hardware
- Verify arcade signal generation
- Debug scoring logic

### **2. Demonstration**
- Show complete PBT system operation
- Visualize waveform processing
- Demonstrate scoring system

### **3. Development**
- Test new features safely
- Validate algorithm changes
- Performance testing

### **4. Training**
- Learn PBT system operation
- Understand waveform processing
- Practice with oscilloscope

## 🔧 Troubleshooting

### **Arduino Not Detected**
```bash
# Check USB connection
ls /dev/ttyUSB* /dev/ttyACM*

# Install arduino-cli
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
```

### **No Waveform on Oscilloscope**
- Check Pin 3 connection
- Verify Arduino is running simulator
- Check oscilloscope settings (DC coupling, 1V/div)

### **Web Interface Not Updating**
- Check Arduino connection
- Verify serial port (/dev/ttyUSB0)
- Check browser console for errors

### **No Arcade Signals**
- Check Pin 6 and Pin 5 connections
- Verify Arduino GPIO commands
- Check serial communication

## 📁 File Structure

```
SICK7/SICK-App/
├── arduino_pbt_simulator.ino    # Arduino simulator code
├── pbt_tester.py                # Pi tester with waveform processing
├── templates/pbt_tester.html    # Web interface with waveform display
├── start_arduino_simulator.sh   # Arduino upload script
├── start_tester.sh              # Pi tester startup script
└── COMPLETE_SIMULATION_README.md # This documentation
```

## 🎉 Benefits

1. **Complete Simulation** - Looks exactly like real PBT system
2. **Oscilloscope Compatible** - Real waveforms for verification
3. **Real Arcade Signals** - Actual GPIO control
4. **Visual Interface** - Real-time waveform display
5. **Safe Testing** - No physical PBT hardware needed
6. **Educational** - Learn how PBT system works
7. **Debugging** - Identify issues easily
8. **Demonstration** - Show system operation

## 🚀 Next Steps

1. **Upload Arduino simulator** to your Arduino
2. **Connect oscilloscope** probes to pins 3, 6, 5
3. **Start Pi tester** and open web interface
4. **Click "Start Simulation"** to begin
5. **Watch the magic** - realistic PBT simulation!

This system gives you a **complete PBT simulation** that looks and behaves exactly like the real system, perfect for testing, debugging, and demonstration! 🎯
