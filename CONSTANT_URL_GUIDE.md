# Getting a Constant URL for Your SICK Sensor Dashboard

## The Problem
- **ngrok free tier**: Random URLs that change every restart (e.g., `https://abc123.ngrok.io`)
- **Your need**: Permanent URL for multi-sensor dashboard

---

## ✅ Best Solutions (Ranked)

### 🥇 Option 1: ngrok with Custom Domain (Paid - $8/month)

**Pros:**
- ✅ Your own domain: `sick.yourdomain.com`
- ✅ Permanent URL
- ✅ Automatic HTTPS
- ✅ Easy setup
- ✅ Works through firewalls

**Setup:**
```bash
# Upgrade to ngrok paid plan ($8/mo)
# Add custom domain in dashboard

ngrok http --domain=sick.yourdomain.com 5000
```

**Cost:** $8/month (or $84/year)

---

### 🥈 Option 2: Cloudflare Tunnel (FREE! 🎉)

**Like ngrok but FREE with custom domains!**

**Pros:**
- ✅ **Completely FREE**
- ✅ Custom subdomain: `sick.yourdomain.com` or use Cloudflare's free domain
- ✅ Permanent URL
- ✅ Automatic HTTPS
- ✅ Better performance than ngrok
- ✅ No bandwidth limits

**Setup:**

1. **Install cloudflared on Raspberry Pi:**
```bash
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm
sudo mv cloudflared-linux-arm /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared
```

2. **Login to Cloudflare:**
```bash
cloudflared tunnel login
```

3. **Create a tunnel:**
```bash
cloudflared tunnel create sick-sensors
```

4. **Create config file:**
```bash
nano ~/.cloudflared/config.yml
```

Add:
```yaml
tunnel: sick-sensors
credentials-file: /home/pi/.cloudflared/<TUNNEL-ID>.json

ingress:
  - hostname: sick.yourdomain.com
    service: http://localhost:5000
  - service: http_status:404
```

5. **Setup DNS (in Cloudflare dashboard):**
```bash
cloudflared tunnel route dns sick-sensors sick.yourdomain.com
```

6. **Run tunnel:**
```bash
cloudflared tunnel run sick-sensors
```

**Make it permanent:**
```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

**Cost:** FREE! (Just need a domain - $10-12/year, or use free Cloudflare Workers domain)

---

### 🥉 Option 3: DuckDNS + Port Forwarding (FREE)

**Free dynamic DNS with your own subdomain**

**Pros:**
- ✅ FREE forever
- ✅ Your subdomain: `sick-sensors.duckdns.org`
- ✅ Permanent URL
- ⚠️ Requires port forwarding on router

**Setup:**

1. **Sign up at [DuckDNS.org](https://www.duckdns.org)** (free, no credit card)

2. **Create subdomain:** `sick-sensors.duckdns.org`

3. **Install DuckDNS updater on Pi:**
```bash
mkdir ~/duckdns
cd ~/duckdns
nano duck.sh
```

Add:
```bash
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=sick-sensors&token=YOUR-TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -
```

```bash
chmod +x duck.sh
```

4. **Auto-update IP every 5 minutes:**
```bash
crontab -e
```

Add:
```
*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

5. **Setup port forwarding:**
- Login to router (usually `192.168.1.1`)
- Forward external port `80` → Pi's IP port `5000`
- Or use different port like `8080` → `5000`

6. **Access at:** `http://sick-sensors.duckdns.org` (or `:8080` if using that port)

**For HTTPS (recommended):**
```bash
# Install nginx and certbot
sudo apt install nginx certbot python3-certbot-nginx

# Get free SSL certificate
sudo certbot --nginx -d sick-sensors.duckdns.org
```

**Cost:** FREE!

---

### 🏅 Option 4: Tailscale + Custom Domain (FREE)

**Private VPN with custom domain**

**Pros:**
- ✅ FREE
- ✅ Secure (not publicly accessible)
- ✅ MagicDNS: `pi.tail-scale.ts.net`
- ✅ Can add custom domain
- ✅ No port forwarding

**Setup:**

1. **Install Tailscale (you may have done this):**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

2. **Enable MagicDNS** in Tailscale admin panel

3. **Access at:** `http://pi:5000` or `http://100.x.x.x:5000`

4. **(Optional) Add custom domain:**
- In Tailscale admin panel
- Add DNS record pointing to your Pi's Tailscale IP

**Cost:** FREE for personal use

---

### 🚀 Option 5: Buy Cheap Domain + Use Any Method (Best for Capstone)

**Get a real domain for ~$1-12/year**

**Recommended registrars:**
- **Namecheap**: `.xyz` for $1/year, `.com` for $9/year
- **Cloudflare**: `.com` for $10/year
- **Porkbun**: Various cheap domains

**Then use:**
- Cloudflare Tunnel (FREE)
- Or ngrok with custom domain ($8/mo)
- Or DuckDNS for free subdomain

---

## 📊 Comparison Table

| Solution | Cost/Year | Setup Difficulty | URL Example | Best For |
|----------|-----------|------------------|-------------|----------|
| **Cloudflare Tunnel** | $10-12 (domain only) | ⭐⭐⭐ Medium | `sick.yourdomain.com` | **Best overall!** |
| **ngrok Paid** | $96 | ⭐ Easy | `sick.yourdomain.com` | If you value simplicity |
| **DuckDNS** | FREE | ⭐⭐⭐ Medium | `sick-sensors.duckdns.org` | Budget option |
| **Tailscale** | FREE | ⭐⭐ Easy | `pi.tail-scale.ts.net` | Private/secure access |
| **Port Forward** | FREE | ⭐⭐⭐⭐ Hard | `your-ip:5000` | Not recommended |

---

## 🎯 My Recommendation for Your Capstone

### **For Multi-Sensor Dashboard:**

**Best: Cloudflare Tunnel + Cheap Domain**

**Why:**
1. ✅ **FREE** (except $1-12 domain/year)
2. ✅ Permanent URL: `sensors.yourdomain.com`
3. ✅ Professional for capstone
4. ✅ Can add subdomains later:
   - `sensors.yourdomain.com` - Main dashboard
   - `pbt.yourdomain.com` - PBT only
   - `pmt.yourdomain.com` - PMT only
   - `api.yourdomain.com` - API endpoint

**Setup steps:**
```bash
# 1. Buy domain ($1-12 at Namecheap/Cloudflare)
#    e.g., "sick-sensors.xyz" for $1/year

# 2. Add to Cloudflare (free account)

# 3. Install Cloudflare Tunnel on Pi
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm
sudo mv cloudflared-linux-arm /usr/local/bin/cloudflared
sudo chmod +x /usr/local/bin/cloudflared

# 4. Setup tunnel
cloudflared tunnel login
cloudflared tunnel create sick-sensors
cloudflared tunnel route dns sick-sensors sensors.yourdomain.com

# 5. Configure
nano ~/.cloudflared/config.yml

# 6. Run as service
sudo cloudflared service install
sudo systemctl start cloudflared
```

---

## 🔧 Alternative: Use Free Subdomain Services

If you don't want to buy a domain at all:

### **Free Subdomain Options:**
1. **Cloudflare Workers** - `yourapp.workers.dev` (free)
2. **FreeDNS** - `yourapp.freeddns.org` (free)
3. **DuckDNS** - `yourapp.duckdns.org` (free)
4. **No-IP** - `yourapp.ddns.net` (free)

---

## 📱 Multi-Sensor Architecture

Since you're adding more sensors, here's how to structure it:

### **Option A: Single App, Multiple Pages**
```
sensors.yourdomain.com/          → Dashboard (all sensors)
sensors.yourdomain.com/pbt       → PBT sensor page
sensors.yourdomain.com/pmt       → PMT sensor page
sensors.yourdomain.com/gm        → GM counter page
```

### **Option B: Subdomains** (cleaner)
```
sensors.yourdomain.com           → Main dashboard
pbt.yourdomain.com              → PBT sensor
pmt.yourdomain.com              → PMT sensor
gm.yourdomain.com               → GM counter
```

With Cloudflare Tunnel, you can set up multiple tunnels/routes:
```yaml
ingress:
  - hostname: sensors.yourdomain.com
    service: http://localhost:5000
  - hostname: pbt.yourdomain.com
    service: http://localhost:5001
  - hostname: pmt.yourdomain.com
    service: http://localhost:5002
```

---

## 💡 Quick Decision Guide

### If you need it NOW for free:
→ **DuckDNS** (free subdomain, 30 min setup)

### If you want professional URL (recommended):
→ **Buy $1 domain + Cloudflare Tunnel** (1-2 hours setup)

### If you want easiest paid solution:
→ **ngrok paid plan** ($8/month, 5 min setup)

### If you want private/secure only:
→ **Tailscale** (free, 15 min setup)

---

## 🚀 Implementation Scripts

I'll create automation scripts for each option in a separate file. Let me know which you prefer!

---

## 📝 My Top Pick for You

**Cloudflare Tunnel with a $1 .xyz domain**

**Total cost:** $1/year  
**Setup time:** 1-2 hours  
**Result:** `sick-sensors.xyz` or `sensors.yourdomain.com`  

Perfect for a capstone project - looks professional, costs almost nothing, and you can expand it for all your sensors!

Would you like me to create detailed setup scripts for Cloudflare Tunnel?

