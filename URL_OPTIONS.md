# SICK Sensors - URL Options for Multi-Sensor Dashboard

## 🎯 Your Current Setup
- ✅ ngrok temporary URL: `https://7e3ec373ef66.ngrok-free.app/`
- ⚠️ Changes every time you restart ngrok
- ❌ Not ideal for multi-sensor dashboard

---

## ✨ Get a Permanent URL (For PBT + PMT + GM + Future Sensors)

### 🥇 **Best: Cloudflare Tunnel (FREE!)**

**What you get:**
- 🎯 Your own domain: `sick-sensors.com` or `sensors.yourdomain.com`
- 💰 Cost: $1-12/year for domain (tunnel is FREE!)
- 🔒 Automatic HTTPS
- 📡 Works through any firewall
- 🚀 Better performance than ngrok

**Quick setup:**
```bash
# On Raspberry Pi
./setup_cloudflare_tunnel.sh

# Then follow the prompts to:
# 1. Buy a cheap domain ($1/year at Namecheap)
# 2. Add it to Cloudflare (free)
# 3. Configure tunnel
# 4. Done!
```

**Result:** `sensors.yourdomain.com` - permanent, professional URL!

---

### 🥈 **ngrok with Custom Domain**

**What you get:**
- 🎯 Your domain: `sensors.yourdomain.com`
- 💰 Cost: $8/month ($96/year)
- ⚡ Easiest setup
- 🔒 Automatic HTTPS

**Setup:**
```bash
# Upgrade ngrok to paid plan
# Then:
ngrok http --domain=sensors.yourdomain.com 5000
```

**Result:** Same permanent URL, but costs more

---

### 🥉 **DuckDNS (FREE Subdomain)**

**What you get:**
- 🎯 Free subdomain: `sick-sensors.duckdns.org`
- 💰 Cost: FREE forever
- ⚙️ Requires port forwarding on router

**Setup:**
1. Sign up at duckdns.org (free)
2. Create subdomain: `sick-sensors`
3. Forward port 80 → 5000 on router
4. Access at: `http://sick-sensors.duckdns.org`

---

## 🏗️ Multi-Sensor URL Structure

### **Option A: Single Domain with Paths**
```
sensors.yourdomain.com/          → Main dashboard (all sensors)
sensors.yourdomain.com/pbt       → PBT sensor only
sensors.yourdomain.com/pmt       → PMT sensor only
sensors.yourdomain.com/gm        → GM counter only
sensors.yourdomain.com/api       → API endpoints
```

### **Option B: Subdomains (Cleaner!)**
```
sensors.yourdomain.com           → Main dashboard
pbt.yourdomain.com              → PBT sensor
pmt.yourdomain.com              → PMT sensor
gm.yourdomain.com               → GM counter
api.yourdomain.com              → API
```

With Cloudflare Tunnel, you can easily add multiple subdomains - all FREE!

---

## 💡 My Recommendation

**For your multi-sensor capstone:**

### **Buy a $1 domain + Use Cloudflare Tunnel**

**Why:**
1. ✅ **Professional**: `sick-sensors.xyz` looks better than ngrok
2. ✅ **Cheap**: $1-12/year (vs $96/year for ngrok)
3. ✅ **Scalable**: Easy to add subdomains for each sensor
4. ✅ **Permanent**: URL never changes
5. ✅ **Fast**: Cloudflare CDN performance

**Where to buy cheap domains:**
- **Namecheap**: `.xyz` for $1/year, `.com` for $9/year
- **Cloudflare**: `.com` for $10/year
- **Porkbun**: Various domains $1-15/year

---

## 🚀 Quick Start

### **Step 1: Choose Your Domain**
```bash
# Examples of what you could get:
sick-sensors.xyz       → $1/year
sick-capstone.com      → $9/year
adriel-sick.dev        → $12/year
```

### **Step 2: Setup Cloudflare Tunnel**
```bash
# On Raspberry Pi
./setup_cloudflare_tunnel.sh
```

### **Step 3: Configure for Multiple Sensors**
Edit `~/.cloudflared/config.yml`:
```yaml
tunnel: sick-sensors
credentials-file: /home/pi/.cloudflared/YOUR-TUNNEL-ID.json

ingress:
  # Main dashboard
  - hostname: sensors.yourdomain.com
    service: http://localhost:5000
  
  # PBT sensor (runs on port 5001)
  - hostname: pbt.yourdomain.com
    service: http://localhost:5001
  
  # PMT sensor (runs on port 5002)
  - hostname: pmt.yourdomain.com
    service: http://localhost:5002
  
  # GM counter (runs on port 5003)
  - hostname: gm.yourdomain.com
    service: http://localhost:5003
  
  # Catch-all
  - service: http_status:404
```

### **Step 4: Run as Service**
```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

**Done!** Your sensors are now at permanent URLs! 🎉

---

## 📊 Cost Comparison (Annual)

| Solution | Year 1 | Ongoing | URL Quality |
|----------|--------|---------|-------------|
| **ngrok free** | FREE | FREE | Random (changes) |
| **Cloudflare + domain** | $1-12 | $1-12 | Professional ⭐⭐⭐⭐⭐ |
| **ngrok paid** | $96 | $96 | Professional ⭐⭐⭐⭐⭐ |
| **DuckDNS** | FREE | FREE | Good ⭐⭐⭐ |
| **Tailscale** | FREE | FREE | Private only ⭐⭐⭐ |

---

## 🔗 URL Examples

### **What You Have Now:**
```
https://7e3ec373ef66.ngrok-free.app/  ← Random, changes every restart
```

### **What You Could Have:**
```
https://sensors.sick-capstone.com/    ← Professional, permanent
https://pbt.sick-capstone.com/        ← PBT sensor
https://pmt.sick-capstone.com/        ← PMT sensor
https://gm.sick-capstone.com/         ← GM counter
```

**Cost difference:** $1-12/year vs $96/year 💰

---

## 📝 Next Steps

1. ✅ **Read** `CONSTANT_URL_GUIDE.md` for detailed comparison
2. ✅ **Choose** a domain registrar (I recommend Namecheap for $1 .xyz)
3. ✅ **Run** `./setup_cloudflare_tunnel.sh` on your Raspberry Pi
4. ✅ **Configure** for multiple sensors
5. ✅ **Share** your permanent URL with everyone!

---

## 🆘 Need Help?

See these guides:
- `CONSTANT_URL_GUIDE.md` - Detailed comparison of all options
- `DEPLOYMENT.md` - Complete deployment guide
- `DEPLOY_QUICK.md` - Quick reference commands

---

**Pro tip:** Start with ngrok for testing, then switch to Cloudflare Tunnel once you're ready to deploy all sensors. You'll get a professional URL for just $1/year! 🚀

