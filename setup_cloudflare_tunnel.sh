#!/bin/bash

# Cloudflare Tunnel Setup Script for SICK Sensors
# This gives you a FREE permanent URL!

echo "================================================"
echo "   Cloudflare Tunnel Setup - FREE Permanent URL"
echo "================================================"
echo ""

# Check if running on ARM (Raspberry Pi)
ARCH=$(uname -m)
if [[ "$ARCH" == "arm"* ]] || [[ "$ARCH" == "aarch64" ]]; then
    DOWNLOAD_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm"
    echo "✓ Detected ARM architecture (Raspberry Pi)"
elif [[ "$ARCH" == "x86_64" ]]; then
    DOWNLOAD_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    echo "✓ Detected x86_64 architecture"
else
    echo "⚠️  Unsupported architecture: $ARCH"
    echo "Please download cloudflared manually from:"
    echo "https://github.com/cloudflare/cloudflared/releases"
    exit 1
fi

echo ""

# Check if cloudflared is already installed
if command -v cloudflared &> /dev/null; then
    echo "✓ cloudflared is already installed"
    cloudflared --version
else
    echo "Installing cloudflared..."
    
    # Download
    wget -q --show-progress "$DOWNLOAD_URL" -O /tmp/cloudflared
    
    # Install
    sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
    sudo chmod +x /usr/local/bin/cloudflared
    
    echo "✓ cloudflared installed successfully"
fi

echo ""
echo "================================================"
echo "   Next Steps:"
echo "================================================"
echo ""
echo "1. Login to Cloudflare (this will open a browser):"
echo "   cloudflared tunnel login"
echo ""
echo "2. Create a tunnel:"
echo "   cloudflared tunnel create sick-sensors"
echo ""
echo "3. Get your tunnel ID from the output above, then create config:"
echo "   mkdir -p ~/.cloudflared"
echo "   nano ~/.cloudflared/config.yml"
echo ""
echo "4. Add this to config.yml (replace TUNNEL-ID and YOUR-DOMAIN):"
echo ""
echo "   tunnel: sick-sensors"
echo "   credentials-file: /home/$(whoami)/.cloudflared/TUNNEL-ID.json"
echo ""
echo "   ingress:"
echo "     - hostname: sensors.YOUR-DOMAIN.com"
echo "       service: http://localhost:5000"
echo "     - service: http_status:404"
echo ""
echo "5. Route DNS (replace with your domain):"
echo "   cloudflared tunnel route dns sick-sensors sensors.YOUR-DOMAIN.com"
echo ""
echo "6. Test the tunnel:"
echo "   cloudflared tunnel run sick-sensors"
echo ""
echo "7. If it works, install as service:"
echo "   sudo cloudflared service install"
echo "   sudo systemctl enable cloudflared"
echo "   sudo systemctl start cloudflared"
echo ""
echo "================================================"
echo "   Domain Options:"
echo "================================================"
echo ""
echo "Option 1: Buy a cheap domain ($1-12/year)"
echo "  - Namecheap: .xyz domains for ~$1/year"
echo "  - Cloudflare: .com domains for ~$10/year"
echo "  - Porkbun: Various cheap options"
echo ""
echo "Option 2: Use free subdomain services"
echo "  - Cloudflare Workers (yourapp.workers.dev)"
echo "  - Check CONSTANT_URL_GUIDE.md for more options"
echo ""
echo "================================================"
echo ""
echo "For detailed instructions, see:"
echo "  - CONSTANT_URL_GUIDE.md"
echo "  - https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/"
echo ""
echo "Installation complete! Follow the steps above."
echo ""

