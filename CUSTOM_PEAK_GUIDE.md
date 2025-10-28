# Custom Peak Input Guide

## 🎯 **New Feature: Custom Peak Input**

You can now input your own peak amplitude values and generate specific waveforms on Pin 3!

## 🔧 **How to Use Custom Peak Input**

### **1. Web Interface Controls**
- **Peak Amplitude Input**: Enter any value from 0-200 ADC
- **"Generate Custom Peak" Button**: Creates a peak with your specified amplitude
- **Range**: 0-200 ADC (0-5V)
- **Recommended**: 24-100 ADC for testing

### **2. Step-by-Step Usage**

1. **Start the system**:
   ```bash
   ./start_tester.sh
   ```

2. **Open web interface**: `http://localhost:5002`

3. **Start simulation**: Click "Start Simulation"

4. **Input custom peak**:
   - Enter desired amplitude (e.g., 45 ADC)
   - Click "Generate Custom Peak"

5. **Watch the results**:
   - **Oscilloscope Pin 3**: You'll see a spike with your exact amplitude
   - **Web interface**: Shows the custom peak in real-time
   - **Pi processing**: Calculates pulse width and sends arcade signal

## 📊 **Peak Amplitude Reference**

| ADC Value | Voltage | Description | Expected Pulse Width |
|-----------|---------|-------------|---------------------|
| 0-23 | 0-0.11V | Below threshold | No trigger |
| 24-30 | 0.11-0.15V | Low score | 80-100ms |
| 30-45 | 0.15-0.22V | Medium score | 40-80ms |
| 45-60 | 0.22-0.29V | High score | 20-40ms |
| 60+ | 0.29V+ | Very high | 10-20ms |

## 🎮 **Testing Scenarios**

### **Test Low Score (30 ADC)**
- Input: 30
- Expected: Long pulse (80-100ms)
- Oscilloscope: Small spike above baseline

### **Test Medium Score (45 ADC)**
- Input: 45
- Expected: Medium pulse (40-80ms)
- Oscilloscope: Medium spike

### **Test High Score (60 ADC)**
- Input: 60
- Expected: Short pulse (20-40ms)
- Oscilloscope: Large spike

### **Test Below Threshold (20 ADC)**
- Input: 20
- Expected: No trigger
- Oscilloscope: Small spike, no arcade signal

## 🔍 **What You'll See**

### **On Oscilloscope (Pin 3)**:
- **Baseline**: ~2.5V (512 ADC)
- **Custom Peak**: Exact amplitude you specified
- **Shape**: Bell curve (smooth rise and fall)
- **Duration**: ~50ms

### **On Web Interface**:
- **Real-time waveform**: Shows your custom peak
- **Live statistics**: Updates with peak detection
- **Arcade signal**: Generated based on your peak

### **In Terminal**:
```
# CUSTOM PEAK REQUESTED: Amplitude=45 ADC (0.22V)
# CUSTOM PEAK GENERATED: Amplitude=45 ADC (0.22V)
Peak detected: 45.0 ADC
Pulse #1: Peak=45.0 → 65ms
```

## 🎯 **Benefits of Custom Peak Input**

1. **Precise Testing** - Test exact peak values
2. **Reproducible Results** - Same peak every time
3. **Algorithm Validation** - Verify scoring logic
4. **Educational** - Learn how different peaks affect scoring
5. **Debugging** - Test specific edge cases

## 🔧 **Technical Details**

### **Arduino Command**:
```
CUSTOM_PEAK:45
```

### **Peak Generation**:
- **Amplitude**: Your specified value (0-200 ADC)
- **Shape**: Bell curve using sine function
- **Duration**: 50 samples at 800Hz = 62.5ms
- **Baseline**: 512 ADC (2.5V)

### **Pi Processing**:
- **Same algorithm** as production system
- **Peak detection** when envelope > 24 ADC
- **Pulse calculation** using inverse mapping
- **Arcade signal** sent via GPIO

## 🚀 **Quick Start**

1. **Upload Arduino simulator**: `./start_arduino_simulator.sh`
2. **Start Pi tester**: `./start_tester.sh`
3. **Open web interface**: `http://localhost:5002`
4. **Start simulation**: Click "Start Simulation"
5. **Test custom peak**: Enter 50, click "Generate Custom Peak"
6. **Watch oscilloscope**: You'll see a 50 ADC peak on Pin 3!

**Now you have complete control over the peak amplitude for precise testing!** 🎯
