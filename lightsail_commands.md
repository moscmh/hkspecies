# Lightsail Deployment Commands

## Manual Setup Steps
```bash
# 1. SSH into your Lightsail instance
ssh -i ~/.ssh/LightsailDefaultKey-us-east-1.pem ubuntu@YOUR_INSTANCE_IP

# 2. Install nginx
sudo apt update && sudo apt install -y nginx

# 3. Clone your repository
cd /var/www
sudo git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git hkspecies
sudo chown -R ubuntu:ubuntu /var/www/hkspecies
cd /var/www/hkspecies

# 4. Install Python dependencies
python3.11 -m pip install fastapi uvicorn[standard] geopandas pandas torch torchvision numpy scikit-learn

# 5. Deploy service
chmod +x deploy_service.sh
./deploy_service.sh
```

## Service Management
```bash
# Start service
sudo systemctl start hkspecies

# Stop service
sudo systemctl stop hkspecies

# Restart service
sudo systemctl restart hkspecies

# Check status
sudo systemctl status hkspecies

# View logs
sudo journalctl -u hkspecies -f

# Test direct access
curl http://localhost:8000
```

## Update App
```bash
# Pull latest changes
cd /var/www/hkspecies
git pull origin main

# Restart service
sudo systemctl restart hkspecies

# Check if running on port 8000
sudo netstat -tlnp | grep :8000
```

## Troubleshooting
```bash
# Check nginx status
sudo systemctl status nginx

# Check app logs
sudo journalctl -u hkspecies --no-pager

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```