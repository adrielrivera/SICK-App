# Arduino PBT Tester Code

## Overview
This Arduino code is specifically designed for the SICK7 PBT Tester system. It handles GPIO control for the arcade machine without any PBT sensor reading.

## Features
- **GPIO Control**: Controls arcade motherboard pins 5 and 6
- **Serial Commands**: Responds to commands from Pi
- **Status LED**: Visual feedback for activity
- **No PBT Sensor**: Only handles GPIO control

## Hardware Connections
```
Arcade Pin 5 ──── Arduino Pin 5 (ACTIVE signal)
Arcade Pin 6 ──── Arduino Pin 6 (START signal)  
Arcade GND  ──── Arduino GND
```

## Commands
The Arduino responds to these serial commands:
- `PIN5_HIGH` - Set Pin 5 HIGH (5V)
- `PIN5_LOW` - Set Pin 5 LOW (0V)
- `PIN6_HIGH` - Set Pin 6 HIGH (5V) 
- `PIN6_LOW` - Set Pin 6 LOW (0V)
- `RESET_GPIO` - Reset pins to default states
- `STATUS` - Report current pin states

## Upload Instructions

### Using the upload script (Recommended)
```bash
cd ~/SICK7/SICK-App/arduino_pbt_tester
./upload.sh
```

### Using Arduino IDE
1. Open `arduino_pbt_tester.ino` in Arduino IDE
2. Select Arduino Uno board
3. Select correct port (`/dev/ttyUSB0` or `/dev/ttyACM0`)
4. Click Upload

## Usage
1. Upload this code to your Arduino
2. Connect to arcade machine as shown above
3. Run `./start_tester.sh` on the Pi
4. Use the web interface to test PBT scoring

## Integration
This Arduino code works with:
- `pbt_tester.py` - Main Pi application
- `start_tester.sh` - Pi startup script
- Web interface on `http://localhost:5002`

The Pi generates PBT waveforms and sends GPIO commands to this Arduino for arcade control.
