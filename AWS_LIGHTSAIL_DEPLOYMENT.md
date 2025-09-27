# AWS Lightsail Deployment Guide

## Overview
Deploy your Hong Kong Species API to AWS Lightsail for $10/month (2GB RAM, 1 vCPU).

## Step 1: Create Lightsail Instance

1. Go to [AWS Lightsail Console](https://lightsail.aws.amazon.com/)
2. Click "Create instance"
3. Choose "Linux/Unix" platform
4. Select "Ubuntu 22.04 LTS"
5. Choose "$10 USD" plan (2GB RAM, 1 vCPU)
6. Name your instance (e.g., "hk-species-api")
7. Click "Create instance"

## Step 2: Upload Your Code

1. Wait for instance to be running
2. Click "Connect using SSH"
3. Upload your project files:
   ```bash
   # On your local machine
   scp -r . ubuntu@YOUR_INSTANCE_IP:~/hkspecies/
   ```

## Step 3: Deploy Application

SSH into your instance and run:
```bash
cd ~/hkspecies
chmod +x lightsail-deploy.sh
./lightsail-deploy.sh
```

## Step 4: Set Up Auto-Start Service

```bash
# Copy service file
sudo cp systemd-service.txt /etc/systemd/system/hkspecies.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable hkspecies
sudo systemctl start hkspecies

# Check status
sudo systemctl status hkspecies
```

## Step 5: Configure Firewall

```bash
# Open port 8000
sudo ufw allow 8000
sudo ufw enable
```

## Step 6: Access Your API

Your API will be available at:
`http://YOUR_INSTANCE_IP:8000`

## Cost: $10/month

- 2GB RAM, 1 vCPU
- 40GB SSD storage
- 2TB data transfer

## Monitoring

Check logs:
```bash
sudo journalctl -u hkspecies -f
```

Restart service:
```bash
sudo systemctl restart hkspecies
```