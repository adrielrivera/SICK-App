#!/bin/bash

# SICK PBT Sensor - Raspberry Pi Deployment Script

echo "=========================================="
echo "   SICK PBT Sensor - Pi Deployment"
echo "=========================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /etc/rpi-issue ]; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "This script is designed for Raspberry Pi deployment."
    echo ""
fi

# Update service file with correct paths
INSTALL_DIR=$(pwd)
echo "Installation directory: $INSTALL_DIR"
echo ""

# Create updated service file
cat > sick-pbt.service << EOF
[Unit]
Description=SICK PBT Sensor Web App
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
ExecStart=$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/app.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Service file updated with current paths"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

echo ""
echo "=========================================="
echo "To install as system service, run:"
echo ""
echo "  sudo cp sick-pbt.service /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable sick-pbt.service"
echo "  sudo systemctl start sick-pbt.service"
echo ""
echo "To check status:"
echo "  sudo systemctl status sick-pbt.service"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u sick-pbt.service -f"
echo "=========================================="
echo ""

# Get IP address
IP=$(hostname -I | awk '{print $1}')
if [ -n "$IP" ]; then
    echo "Your app will be accessible at:"
    echo "  http://$IP:5000"
    echo ""
fi

echo "Deployment preparation complete!"

