# SICK PBT Sensor - Deployment Guide

## 🌍 Deployment Overview

Since your application needs **hardware access** (Arduino via serial port), it **must run on the Raspberry Pi**. However, you can make it accessible from anywhere!

---

## 📍 Deployment Options

### ✅ Option 1: Local Network Access (Easiest)
**Access from devices on same WiFi/network**
- No internet required
- Fast and secure
- Perfect for lab/classroom use

### 🌐 Option 2: Internet Access via ngrok (Quick & Easy)
**Temporary public URL without router configuration**
- Free tier available
- No port forwarding needed
- Perfect for demos/testing

### 🔒 Option 3: VPN Access via Tailscale (Secure)
**Private network accessible from anywhere**
- Secure and private
- No port forwarding
- Best for remote access

### 🚀 Option 4: Public Internet via Port Forwarding
**Permanent public access**
- Requires router access
- Need dynamic DNS or static IP
- Good for permanent installations

---

## 🔧 Option 1: Local Network Deployment

### Step 1: Deploy on Raspberry Pi

Transfer files to Raspberry Pi:
```bash
# On your Mac (in the project directory)
scp -r * pi@raspberrypi.local:~/SICK-App/
```

Or use git:
```bash
# Initialize git repo (on Mac)
git init
git add .
git commit -m "Initial commit"

# On Raspberry Pi
git clone <your-repo-url>
cd SICK-App
```

### Step 2: Run Deployment Script

On the Raspberry Pi:
```bash
cd ~/SICK-App
./deploy_pi.sh
```

### Step 3: Install as Service

```bash
sudo cp sick-pbt.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sick-pbt.service
sudo systemctl start sick-pbt.service
```

### Step 4: Access Locally

Find Pi's IP:
```bash
hostname -I
```

Access from any device on same network:
```
http://192.168.1.XXX:5000
```

---

## 🌐 Option 2: Internet Access with ngrok

### What is ngrok?
ngrok creates a secure tunnel to your localhost, giving you a public URL without port forwarding.

### Step 1: Install ngrok on Raspberry Pi

```bash
# Download ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm.tgz

# Extract
tar xvzf ngrok-v3-stable-linux-arm.tgz

# Move to /usr/local/bin
sudo mv ngrok /usr/local/bin/

# Sign up at https://ngrok.com and get auth token
ngrok config add-authtoken <your-auth-token>
```

### Step 2: Start Your App

```bash
cd ~/SICK-App
python3 app.py
```

### Step 3: Start ngrok Tunnel

In another terminal:
```bash
ngrok http 5000
```

You'll get a public URL like:
```
https://abc123.ngrok.io → http://localhost:5000
```

### Step 4: Share the URL

Anyone can access your app at: `https://abc123.ngrok.io`

### Pros & Cons
✅ No router configuration  
✅ HTTPS automatically  
✅ Easy to set up  
❌ Free tier has random URLs  
❌ Tunnel stops when Pi restarts  

### Make it Persistent

Create ngrok service:
```bash
sudo nano /etc/systemd/system/ngrok.service
```

```ini
[Unit]
Description=ngrok tunnel
After=network.target

[Service]
Type=simple
User=pi
ExecStart=/usr/local/bin/ngrok http 5000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable ngrok.service
sudo systemctl start ngrok.service
```

---

## 🔒 Option 3: Secure VPN Access with Tailscale

### What is Tailscale?
Creates a private VPN network. Access your Pi from anywhere as if you're on the same network.

### Step 1: Install Tailscale

On Raspberry Pi:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

### Step 2: Install on Your Devices

- Install Tailscale on your phone/laptop/tablet
- Login with same account
- All devices are now on same private network!

### Step 3: Access Your App

```bash
# On Pi, get Tailscale IP
tailscale ip -4
```

Access from any device with Tailscale:
```
http://100.64.x.x:5000
```

### Pros & Cons
✅ Secure and private  
✅ Works from anywhere  
✅ No public exposure  
✅ Free for personal use  
❌ Requires Tailscale on each device  

---

## 🚀 Option 4: Port Forwarding (Advanced)

### Step 1: Static IP for Raspberry Pi

On Raspberry Pi, set static IP:
```bash
sudo nano /etc/dhcpcd.conf
```

Add:
```
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8
```

### Step 2: Router Port Forwarding

1. Login to your router (usually `192.168.1.1`)
2. Find "Port Forwarding" settings
3. Forward external port `5000` to Pi's IP port `5000`

### Step 3: Get Public IP

```bash
curl ifconfig.me
```

Your app is now at: `http://YOUR_PUBLIC_IP:5000`

### Step 4: Dynamic DNS (Optional)

If you don't have static IP:
1. Sign up for free DDNS (DuckDNS, No-IP, etc.)
2. Install DDNS client on Pi
3. Get a domain like `myapp.duckdns.org`

### Security Considerations
⚠️ **Important**: Add authentication if exposing to internet!

Basic auth in Flask:
```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

users = {
    "admin": "your-password"
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')
```

---

## 🐳 Option 5: Cloud Deployment (Advanced)

If you don't need the Arduino (e.g., for demo with test mode):

### Deploy to Render.com (Free Tier)

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: sick-pbt-sensor
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python test_mode.py
    envVars:
      - key: HOST
        value: 0.0.0.0
      - key: PORT
        value: 10000
```

2. Push to GitHub
3. Connect to Render
4. Deploy!

**Note**: This only works with `test_mode.py` (simulated data), not real Arduino.

---

## 📊 Comparison Table

| Method | Difficulty | Cost | Access | Arduino Support | Best For |
|--------|-----------|------|--------|-----------------|----------|
| **Local Network** | ⭐ Easy | Free | Local only | ✅ Yes | Lab/classroom |
| **ngrok** | ⭐⭐ Medium | Free/Paid | Internet | ✅ Yes | Quick demos |
| **Tailscale** | ⭐⭐ Medium | Free | Private VPN | ✅ Yes | Secure remote |
| **Port Forward** | ⭐⭐⭐ Hard | Free | Internet | ✅ Yes | Permanent setup |
| **Cloud** | ⭐⭐⭐ Hard | Free/Paid | Internet | ❌ No | Test mode only |

---

## 🎯 Recommended Setup

### For Your Capstone Project:

**During Development:**
```bash
# Local access for testing
python3 test_mode.py
# Access at http://localhost:5000
```

**For Demos/Presentations:**
```bash
# Use ngrok for quick public access
python3 app.py  # Start app
ngrok http 5000  # Get public URL
# Share URL with audience
```

**For Final Deployment:**
```bash
# Install as service on Pi
./deploy_pi.sh
sudo systemctl enable sick-pbt.service
sudo systemctl start sick-pbt.service

# Use Tailscale for secure remote access
# OR set up port forwarding for public access
```

---

## 🔐 Security Checklist

If exposing to internet:

- [ ] Add authentication (username/password)
- [ ] Use HTTPS (via ngrok or reverse proxy)
- [ ] Change default SECRET_KEY in config.py
- [ ] Enable firewall on Raspberry Pi
- [ ] Keep software updated
- [ ] Monitor access logs
- [ ] Consider rate limiting

---

## 🆘 Troubleshooting

### Can't Access from Other Devices

1. **Check firewall:**
```bash
sudo ufw status
sudo ufw allow 5000
```

2. **Check app is listening on 0.0.0.0:**
```python
# In config.py
HOST = '0.0.0.0'  # Not '127.0.0.1'
```

3. **Verify Pi's IP:**
```bash
hostname -I
ping 192.168.1.XXX  # From other device
```

### ngrok Issues

1. **Check auth token:**
```bash
ngrok config check
```

2. **View ngrok dashboard:**
```
http://localhost:4040
```

### Service Won't Start

1. **Check logs:**
```bash
sudo journalctl -u sick-pbt.service -n 50
```

2. **Check permissions:**
```bash
ls -la /home/pi/SICK-App
```

3. **Test manually:**
```bash
cd ~/SICK-App
source venv/bin/activate
python3 app.py
```

---

## 📱 Mobile Access Tips

### Create Home Screen Icon (iOS/Android)

1. Open app in mobile browser
2. Tap "Share" or menu (⋯)
3. Select "Add to Home Screen"
4. Now it opens like a native app!

### Optimize for Mobile

The app is already responsive, but you can add to `templates/index.html`:

```html
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="apple-touch-icon" href="/static/icon.png">
```

---

## 🎓 Next Steps

1. ✅ Deploy on Raspberry Pi as service
2. ✅ Test local network access
3. ✅ Set up ngrok for demos
4. ✅ (Optional) Configure Tailscale for remote access
5. ✅ Add authentication if making public
6. ✅ Create home screen icons for mobile users

---

## 📚 Additional Resources

- [ngrok Documentation](https://ngrok.com/docs)
- [Tailscale Setup Guide](https://tailscale.com/kb/1017/install/)
- [Raspberry Pi Static IP](https://raspberrypi.stackexchange.com/questions/37920/how-do-i-set-up-networking-wifi-static-ip-address)
- [Flask Security](https://flask.palletsprojects.com/en/3.0.x/security/)
- [DuckDNS Free Dynamic DNS](https://www.duckdns.org/)

---

**Need help? Check the logs and review this guide!** 🚀

