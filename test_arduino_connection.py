#!/usr/bin/env python3
"""
Test Arduino Connection - Simple script to test PBT Arduino
"""

import serial
import time
import sys

def test_arduino_connection(port="/dev/ttyUSB0", baud=115200):
    """Test connection to Arduino and read data."""
    print(f"Testing Arduino connection on {port} @ {baud} baud...")
    
    try:
        ser = serial.Serial(port, baud, timeout=1)
        time.sleep(0.2)
        ser.reset_input_buffer()
        print("✅ Connected to Arduino")
        
        # Read data for 10 seconds
        print("Reading data for 10 seconds...")
        start_time = time.time()
        sample_count = 0
        
        while time.time() - start_time < 10:
            try:
                line = ser.readline().decode(errors="ignore").strip()
                if line:
                    if line.startswith("#"):
                        print(f"Arduino: {line}")
                    else:
                        try:
                            value = int(line)
                            sample_count += 1
                            if sample_count % 100 == 0:  # Print every 100 samples
                                print(f"Sample {sample_count}: {value} ADC")
                        except ValueError:
                            pass
            except Exception as e:
                print(f"Error reading: {e}")
                break
        
        print(f"✅ Read {sample_count} samples in 10 seconds")
        print(f"Average sample rate: {sample_count/10:.1f} Hz")
        
        # Test GPIO commands
        print("\nTesting GPIO commands...")
        ser.write(b"STATUS\n")
        time.sleep(0.1)
        
        ser.write(b"PIN6_HIGH\n")
        time.sleep(0.1)
        
        ser.write(b"PIN6_LOW\n")
        time.sleep(0.1)
        
        ser.write(b"RESET_GPIO\n")
        time.sleep(0.1)
        
        print("✅ GPIO commands sent")
        
        ser.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to Arduino: {e}")
        return False

def find_arduino_ports():
    """Find available Arduino ports."""
    import glob
    
    ports = []
    
    # Check common Linux ports
    for pattern in ["/dev/ttyUSB*", "/dev/ttyACM*"]:
        ports.extend(glob.glob(pattern))
    
    return sorted(ports)

if __name__ == "__main__":
    print("=" * 50)
    print("Arduino Connection Test")
    print("=" * 50)
    
    # Find available ports
    ports = find_arduino_ports()
    print(f"Available ports: {ports}")
    
    if not ports:
        print("❌ No Arduino ports found!")
        print("Make sure Arduino is connected via USB")
        sys.exit(1)
    
    # Test each port
    for port in ports:
        print(f"\nTesting {port}...")
        if test_arduino_connection(port):
            print(f"✅ Arduino working on {port}")
            break
    else:
        print("❌ No working Arduino found on any port")
        sys.exit(1)
