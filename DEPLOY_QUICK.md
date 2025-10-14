# 🚀 Quick Deployment Guide

## TL;DR - Choose Your Method

### 🏠 Local Network Only (Easiest)
**Use when:** Testing in lab/classroom on same WiFi

```bash
# On Raspberry Pi
cd ~/SICK-App
./deploy_pi.sh
sudo systemctl start sick-pbt.service

# Access at: http://PI_IP_ADDRESS:5000
```

---

### 🌐 Public Internet - Quick Demo (ngrok)
**Use when:** Need to show someone remotely, quick demos

```bash
# On Raspberry Pi
# Terminal 1
python3 app.py

# Terminal 2
ngrok http 5000

# Share the https://xxxx.ngrok.io URL
```

**Setup ngrok:**
1. Sign up: https://ngrok.com
2. `wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm.tgz`
3. `tar xvzf ngrok-v3-stable-linux-arm.tgz`
4. `sudo mv ngrok /usr/local/bin/`
5. `ngrok config add-authtoken YOUR_TOKEN`

---

### 🔒 Secure Remote Access (Tailscale)
**Use when:** Want permanent secure access from anywhere

```bash
# On Raspberry Pi
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Start service
sudo systemctl start sick-pbt.service

# Install Tailscale on your phone/laptop
# Access at: http://100.x.x.x:5000
```

---

### 🌍 Permanent Public Access (Port Forward)
**Use when:** Need permanent public URL (advanced)

1. Set Pi static IP: `192.168.1.100`
2. Router: Forward port `5000` to Pi
3. Get public IP: `curl ifconfig.me`
4. (Optional) Setup DuckDNS for domain name
5. **⚠️ ADD AUTHENTICATION!**

---

## 📋 Transfer Files to Raspberry Pi

### Method 1: SCP (from Mac)
```bash
cd /Users/adrielrivera/Documents/SICK7/SICK-App
scp -r * pi@raspberrypi.local:~/SICK-App/
```

### Method 2: Git (recommended)
```bash
# On Mac
git init
git add .
git commit -m "Initial commit"
git remote add origin YOUR_GITHUB_REPO
git push -u origin main

# On Pi
git clone YOUR_GITHUB_REPO
cd SICK-App
```

### Method 3: USB Drive
1. Copy folder to USB
2. Insert in Pi
3. `cp -r /media/usb/SICK-App ~/`

---

## ⚡ Quick Commands Reference

### Check if service is running
```bash
sudo systemctl status sick-pbt.service
```

### View live logs
```bash
sudo journalctl -u sick-pbt.service -f
```

### Restart service
```bash
sudo systemctl restart sick-pbt.service
```

### Stop service
```bash
sudo systemctl stop sick-pbt.service
```

### Find Pi IP address
```bash
hostname -I
```

### Test without service
```bash
cd ~/SICK-App
python3 test_mode.py  # Simulated data
# or
python3 app.py  # Real Arduino
```

---

## 🔐 Security (if making public)

### Quick password protection
```bash
pip install flask-httpauth
```

Add to `app.py`:
```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.verify_password
def verify(username, password):
    if username == "admin" and password == "YOUR_PASSWORD":
        return username

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')
```

---

## 📱 Mobile Home Screen Icon

1. Open in mobile browser
2. Tap menu (iOS: Share, Android: ⋮)
3. "Add to Home Screen"
4. Opens like native app!

---

## ✅ Checklist

### Before Deploying:
- [ ] Installed dependencies: `pip install -r requirements.txt`
- [ ] Configured serial port in `config.py`
- [ ] Tested locally: `python3 test_mode.py`
- [ ] Uploaded Arduino sketch: `signal_simulator.ino`

### For Internet Access:
- [ ] Changed SECRET_KEY in `config.py`
- [ ] Added authentication (if public)
- [ ] Tested from another device
- [ ] Documented access URL

### For Production:
- [ ] Deployed as systemd service
- [ ] Enabled auto-start on boot
- [ ] Configured firewall rules
- [ ] Set up monitoring/alerts

---

## 🆘 Common Issues

**Can't connect from phone:**
- Check Pi and phone on same WiFi
- Use `0.0.0.0` in config.py, not `127.0.0.1`
- Check firewall: `sudo ufw allow 5000`

**Service won't start:**
- Check logs: `sudo journalctl -u sick-pbt.service -n 50`
- Verify paths in `sick-pbt.service`
- Test manually: `python3 app.py`

**ngrok not working:**
- Check auth token: `ngrok config check`
- View dashboard: `http://localhost:4040`

---

## 📊 Recommended Setup by Use Case

| Use Case | Method | Why |
|----------|--------|-----|
| **Development** | Local | Fast, simple |
| **Classroom Demo** | Local Network | Same WiFi access |
| **Remote Demo** | ngrok | Quick public URL |
| **Remote Work** | Tailscale | Secure VPN |
| **Capstone Presentation** | ngrok | Easy to share |
| **Permanent Install** | Service + Tailscale | Reliable + secure |

---

## 🎯 Quick Start for Capstone Demo

```bash
# 1. Transfer files to Pi (use git/scp/usb)

# 2. On Pi - Install and run
cd ~/SICK-App
pip3 install -r requirements.txt
python3 test_mode.py

# 3. Access locally
# http://PI_IP:5000

# 4. For remote demo
# Terminal 1: python3 app.py
# Terminal 2: ngrok http 5000
# Share ngrok URL with audience
```

---

**Full details: See `DEPLOYMENT.md`** 📚

