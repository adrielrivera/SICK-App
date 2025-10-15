# 🚨 Raspberry Pi Architecture - Performance Concerns & Solutions

## 📋 Your Current System Load

**Single Raspberry Pi handling:**
1. ⚡ **Web App Server** (Flask + WebSocket) - Real-time PBT data streaming @ 800 Hz
2. 📁 **FTP Server** for SEC110 sensor
3. 🔄 **PBT Processing** - Reading serial @ 800 Hz + envelope detection + pulse generation (GPIO)
4. 📡 **TiM240 Processing** - LiDAR data + processing logic
5. 🌐 **Network Services** - HTTP, WebSocket, FTP

---

## 🚩 Red Flags & Concerns

### 🔴 **Critical Issues:**

#### 1. **Real-Time Processing Bottleneck**
```python
# PBT at 800 Hz = 1.25ms per sample
# If any process blocks for >1.25ms, you drop samples!

Potential blocking operations:
- FTP file transfer (blocks I/O)
- WebSocket broadcast to multiple clients
- TiM240 data processing
- Disk writes
```

**Risk:** Missing PBT events during high system load! ⚠️

---

#### 2. **CPU Saturation**

**Raspberry Pi 4 (quad-core):**
```
Process                  CPU Usage (estimated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PBT Serial + Processing  ~15-25% (one core)
Flask + WebSocket        ~10-20% (spikes with clients)
FTP Server              ~5-15% (during transfers)
TiM240 Processing       ~10-30% (depends on logic)
pigpio daemon           ~5-10%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL                   45-100% (can max out!)
```

**Risk:** System becomes unresponsive during peak load! 🔥

---

#### 3. **I/O Contention**

```
Serial Ports in Use:
├─ /dev/ttyUSB0  → PBT sensor (115200 baud, 800 Hz)
├─ /dev/ttyUSB1  → SEC110 (?)
└─ /dev/ttyUSB2  → TiM240 LiDAR (?)

Network I/O:
├─ HTTP/WebSocket (Port 5000) - Real-time streaming
├─ FTP (Port 21/data ports) - File transfers
└─ SSH (Port 22) - Remote access
```

**Risk:** USB bandwidth saturation, serial buffer overflows! 📉

---

#### 4. **Memory Pressure**

```python
# Memory usage estimates:
PBT buffers (4000 samples * 3 arrays)   ~50 KB
WebSocket clients (10 clients)           ~5-10 MB
Flask app + dependencies                 ~50-100 MB
FTP server + transfers                   ~10-50 MB
TiM240 data buffers                      ~5-20 MB
pigpio daemon                            ~5 MB
System overhead                          ~200 MB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL                                    ~300-450 MB
```

**Raspberry Pi Models:**
- Pi Zero/1: 512 MB RAM ❌ **NOT ENOUGH**
- Pi 2/3: 1 GB RAM ⚠️ **TIGHT**
- Pi 4: 2-8 GB RAM ✅ **Should be OK**

---

#### 5. **Single Point of Failure**

```
If ANY service crashes or hangs:
├─ Entire system can become unresponsive
├─ All sensors go offline
├─ Web interface stops working
└─ Data loss possible
```

**Risk:** Poor reliability for a capstone project! 💔

---

#### 6. **Real-Time Performance Issues**

**Python + Linux are NOT real-time:**
```python
# Your PBT pulse timing code:
pi.wave_send_once(wid)
while pi.wave_tx_busy():
    time.sleep(0.001)  # Can be delayed by OS scheduler!
```

**What can interrupt timing:**
- OS process scheduling
- Python garbage collection
- Disk I/O
- Network interrupts
- Other processes

**Result:** Inconsistent pulse widths! ⏱️

---

## 📊 Performance Testing Results (Estimated)

### **Scenario 1: Light Load** ✅
```
- 1-2 web clients
- No FTP transfer
- Normal TiM240 processing

CPU: 40-60%
Result: Should work fine
```

### **Scenario 2: Demo Day** ⚠️
```
- 10+ students accessing web app
- SEC110 uploading files via FTP
- TiM240 processing data
- PBT detecting events

CPU: 80-100%
Result: Laggy web interface, possible sample drops
```

### **Scenario 3: Peak Load** 🔥
```
- 20+ web clients
- Large FTP transfer
- PBT event happening
- TiM240 heavy processing

CPU: 100%+ (saturated)
Result: System freeze, dropped samples, crashed services
```

---

## ✅ Solutions & Recommendations

### 🎯 **Option 1: Optimize Current Setup** (Quick Fixes)

#### A. **Process Prioritization**
```bash
# Give PBT highest priority (real-time critical)
sudo nice -n -20 python3 pbt_pulse_plot.py &

# Normal priority for web app
python3 app.py &

# Lower priority for FTP
sudo nice -n 10 vsftpd &
```

#### B. **CPU Pinning** (Pi 4 only)
```bash
# Pin PBT to dedicated core
taskset -c 0 python3 pbt_pulse_plot.py &

# Pin web app to different cores
taskset -c 1,2,3 python3 app.py &
```

#### C. **Optimize Code**
```python
# In app.py - reduce update frequency during high load
EMIT_INTERVAL = 0.1  # 10 Hz instead of 20 Hz

# Buffer FTP writes
# Use async I/O where possible
```

---

### 🏆 **Option 2: Distributed Architecture** (Recommended!)

**Split workload across multiple devices:**

```
┌─────────────────────────────────────────────────────┐
│  Raspberry Pi #1 - "Sensor Hub"                     │
│  ├─ PBT Processing (dedicated, real-time critical) │
│  ├─ TiM240 Processing                              │
│  └─ SEC110 data collection                         │
└─────────────────────────────────────────────────────┘
           │
           │ Network (lightweight data stream)
           ↓
┌─────────────────────────────────────────────────────┐
│  Raspberry Pi #2 - "Web Server"                     │
│  ├─ Flask Web App                                   │
│  ├─ WebSocket Server                                │
│  ├─ FTP Server                                      │
│  └─ Data visualization                              │
└─────────────────────────────────────────────────────┘
```

**Benefits:**
- ✅ Pi #1 dedicated to real-time sensor processing
- ✅ Pi #2 handles web traffic without affecting sensors
- ✅ If web server crashes, sensors keep running
- ✅ Can scale web servers horizontally
- ✅ Better reliability

**Cost:** ~$35-75 for second Pi

---

### ⚡ **Option 3: Hybrid Approach** (Best Balance)

**Use what you have, optimize strategically:**

#### **1. Move FTP to Separate Device**
```
Pi: All sensors + Web app
Laptop/PC: FTP server for SEC110
```

**Why:** FTP is the least time-critical service

---

#### **2. Lightweight Web App Mode**
```python
# Add to config.py
LITE_MODE = True  # Reduces data rate and buffer size

if LITE_MODE:
    EMIT_INTERVAL = 0.2     # 5 Hz instead of 20 Hz
    BUFFER_SIZE = 1000      # Smaller buffer
    MAX_CLIENTS = 5         # Limit simultaneous clients
```

---

#### **3. Use Multiple Flask Instances**
```bash
# PBT on port 5000
python3 app.py &

# PMT on port 5001 (separate process)
PORT=5001 python3 app_pmt.py &

# GM on port 5002
PORT=5002 python3 app_gm.py &
```

**Benefits:**
- Isolated processes (one crash doesn't affect others)
- Better CPU distribution across cores
- Easier debugging

---

#### **4. Implement Watchdog**
```python
# watchdog.py - Monitors and restarts crashed services
import subprocess
import time

services = [
    ("PBT", ["python3", "pbt_pulse_plot.py"]),
    ("Web", ["python3", "app.py"]),
]

while True:
    for name, cmd in services:
        # Check if running, restart if not
        # Log crashes
    time.sleep(5)
```

---

### 🔧 **Option 4: Hardware Upgrades**

#### **Use Arduino/ESP32 for PBT Pulse Generation**
```
Raspberry Pi:
├─ Read PBT serial (800 Hz) ✅
├─ Send peak value to Arduino via serial
└─ Arduino generates precise GPIO pulses

Arduino:
└─ Hardware timers for precise pulse width (no jitter!)
```

**Benefits:**
- ✅ Offloads real-time GPIO to dedicated hardware
- ✅ More precise timing
- ✅ Frees up Pi CPU

---

## 📈 Recommended Architecture

### **For Capstone Demo:**

```
┌──────────────────────────────────────┐
│  Raspberry Pi 4 (4GB+ recommended)   │
│                                      │
│  Core 0: PBT Processing (pinned)     │
│  Core 1-3: Web App + WebSocket       │
│                                      │
│  Services:                           │
│  ├─ PBT (high priority, nice -20)   │
│  ├─ Web App (normal priority)       │
│  ├─ TiM240 (normal priority)        │
│  └─ Watchdog (monitors all)         │
└──────────────────────────────────────┘
         │
         │ FTP offloaded to:
         ↓
┌──────────────────────────────────────┐
│  Laptop/Desktop (FTP Server)         │
│  └─ SEC110 file storage              │
└──────────────────────────────────────┘
```

---

## 🧪 Performance Testing Checklist

### **Before Demo Day:**

```bash
# 1. CPU stress test
stress --cpu 4 --timeout 60s
# Run while accessing web app - does it lag?

# 2. Simulate multiple web clients
ab -n 1000 -c 10 http://localhost:5000/
# Apache Bench tool

# 3. Monitor during FTP transfer
watch -n 1 'top -b -n 1 | head -20'
# While transferring large file

# 4. Check dropped samples
# Add counter in PBT code, check if samples are missed

# 5. Memory leak test
# Run for hours, monitor with htop
```

---

## ⚠️ Warning Signs to Watch For

### **During Operation:**

❌ **Bad signs:**
- Web interface becomes unresponsive
- PBT misses events during FTP transfers
- System temperature >80°C (throttling)
- Kernel messages about USB errors
- WebSocket disconnects frequently

✅ **Good signs:**
- Consistent frame rates
- CPU <70% average
- Temperature <70°C
- No dropped serial samples
- Quick web response times

---

## 🎯 Final Recommendations

### **Minimum (Do This!):**
1. ✅ Use Raspberry Pi 4 with 2GB+ RAM
2. ✅ Set process priorities (nice values)
3. ✅ Reduce web update rate to 10 Hz
4. ✅ Limit simultaneous web clients to 10
5. ✅ Add cooling (heatsink + fan)
6. ✅ Monitor temperature and CPU usage

### **Recommended (Better):**
7. ✅ Pin PBT to dedicated CPU core
8. ✅ Move FTP to separate device
9. ✅ Implement watchdog service
10. ✅ Run separate Flask instances per sensor

### **Ideal (Best):**
11. ✅ Use second Raspberry Pi for web server
12. ✅ Offload pulse generation to Arduino
13. ✅ Use Redis for data buffering
14. ✅ Implement proper logging and monitoring

---

## 📊 Quick Decision Matrix

| Pi Model | Single Sensor | 2-3 Sensors | 4+ Sensors + FTP |
|----------|--------------|-------------|------------------|
| **Pi Zero** | ⚠️ Marginal | ❌ No | ❌ No |
| **Pi 3** | ✅ OK | ⚠️ Tight | ❌ No |
| **Pi 4 2GB** | ✅ Good | ✅ OK | ⚠️ Marginal |
| **Pi 4 4GB+** | ✅ Great | ✅ Good | ✅ OK |
| **Pi 5** | ✅ Great | ✅ Great | ✅ Good |
| **2x Pi 4** | ✅ Perfect | ✅ Perfect | ✅ Great |

---

## 🚀 Implementation Priority

### **Phase 1: MVP (Working Demo)**
```bash
# Get it working on single Pi 4
# Accept some performance limitations
# Focus on functionality
```

### **Phase 2: Optimization (Better Performance)**
```bash
# Add process priorities
# Optimize update rates
# Add monitoring
```

### **Phase 3: Production (Reliable)**
```bash
# Distributed architecture
# Watchdog services
# Proper logging
```

---

## 💡 Bottom Line

**Can a single Raspberry Pi handle everything?**
- Pi 4 4GB+: **Yes, with optimization** ✅
- Pi 3 or less: **Probably not reliably** ⚠️

**Should you do it?**
- For capstone demo: **Yes, if you optimize** ✅
- For production/permanent: **No, use distributed architecture** ❌

**Biggest risks:**
1. 🔥 CPU saturation during peak demo
2. ⏱️ Missed PBT events (bad for sensor accuracy)
3. 💔 System crash = everything offline

**Mitigation:**
1. Test under load BEFORE demo day!
2. Have backup plan (run on two Pis if needed)
3. Implement monitoring to catch issues early

---

**Your current plan is ambitious but doable with the right Pi and optimizations!** 🎯

