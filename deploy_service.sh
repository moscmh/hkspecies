#!/bin/bash

# Deploy HK Species app as systemd service on Lightsail
# Run this after cloning repo and installing dependencies

echo "Setting up HK Species service..."

# Create systemd service
sudo tee /etc/systemd/system/hkspecies.service > /dev/null <<EOF
[Unit]
Description=HK Species FastAPI App
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/var/www/hkspecies
Environment="PATH=/usr/bin:/bin"
ExecStart=/usr/bin/python3.11 -m uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
sudo tee /etc/nginx/sites-available/hkspecies > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
EOF

# Enable services
sudo ln -sf /etc/nginx/sites-available/hkspecies /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

sudo systemctl daemon-reload
sudo systemctl enable hkspecies
sudo systemctl restart nginx
sudo systemctl start hkspecies

echo "Service deployed! Check status: sudo systemctl status hkspecies"