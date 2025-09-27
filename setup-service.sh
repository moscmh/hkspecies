#!/bin/bash
# Setup systemd service for persistent running

# Create service file
sudo tee /etc/systemd/system/hkspecies.service > /dev/null <<EOF
[Unit]
Description=Hong Kong Species API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/hkspecies
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable hkspecies
sudo systemctl start hkspecies

echo "✅ Service setup complete!"
echo "📋 Useful commands:"
echo "   sudo systemctl status hkspecies    # Check status"
echo "   sudo systemctl restart hkspecies   # Restart service"
echo "   sudo systemctl logs hkspecies      # View logs"