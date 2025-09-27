# Hong Kong Species API - Deployment Guide

## Quick AWS Lightsail Deployment

### Prerequisites
- AWS CLI installed and configured
- Your application files ready

### 1. Automated Deployment
```bash
# Make the deployment script executable
chmod +x deploy-lightsail.sh

# Run the deployment
./deploy-lightsail.sh
```

### 2. Upload Your Files
After the instance is created, upload your application files:

```bash
# Get your instance IP from the deployment output
INSTANCE_IP="YOUR_INSTANCE_IP"

# Upload all files
rsync -avz -e "ssh -i hk-species-key.pem" \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  ./ ubuntu@$INSTANCE_IP:/opt/hkspecies/

# Set permissions
ssh -i hk-species-key.pem ubuntu@$INSTANCE_IP "sudo chown -R ubuntu:ubuntu /opt/hkspecies/"
```

### 3. Start the Service
```bash
# SSH into the instance
ssh -i hk-species-key.pem ubuntu@$INSTANCE_IP

# Start the service
sudo systemctl start hkspecies
sudo systemctl status hkspecies

# Check logs
sudo journalctl -u hkspecies -f
```

### 4. Update Frontend
Update the API URL in your frontend.html:
```javascript
const API_BASE = 'http://YOUR_INSTANCE_IP:8000/api';
```

### 5. Test the Deployment
```bash
# Test API health
curl http://YOUR_INSTANCE_IP:8000/health

# Test species endpoint
curl http://YOUR_INSTANCE_IP:8000/api/summary

# Access frontend
# Open: http://YOUR_INSTANCE_IP:8000/frontend.html
```

## Manual Deployment Steps

### 1. Create Lightsail Instance
- Go to AWS Lightsail Console
- Create instance with Ubuntu 20.04
- Choose nano ($3.50/month) or micro ($5/month)
- Open port 8000 in networking

### 2. Install Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.9 python3.9-venv python3-pip git
sudo apt install -y gdal-bin libgdal-dev libproj-dev libgeos-dev libspatialindex-dev build-essential python3.9-dev
```

### 3. Setup Application
```bash
mkdir -p /opt/hkspecies
cd /opt/hkspecies
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Create Service
```bash
sudo nano /etc/systemd/system/hkspecies.service
```

Add:
```ini
[Unit]
Description=Hong Kong Species API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/hkspecies
ExecStart=/opt/hkspecies/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable hkspecies
sudo systemctl start hkspecies
```

## Troubleshooting

### Check Service Status
```bash
sudo systemctl status hkspecies
sudo journalctl -u hkspecies -f
```

### Test Prediction System
```bash
cd /opt/hkspecies
source venv/bin/activate
python test_prediction.py
```

### Common Issues

1. **Prediction not working**: Check if all data files are uploaded
2. **Port not accessible**: Ensure port 8000 is open in Lightsail networking
3. **Service won't start**: Check logs and file permissions

### File Structure
```
/opt/hkspecies/
├── app.py                 # Main FastAPI app
├── species_api.py         # Alternative API
├── species_inference.py   # Prediction model
├── api_models.py         # Data models
├── frontend.html         # Web interface
├── requirements.txt      # Python dependencies
├── processed/            # Processed data files
├── boundaries/           # Shapefiles
├── species/             # Raw species data
└── hk.tif               # Hong Kong map
```

## Cost Estimation
- Nano instance: $3.50/month
- Micro instance: $5.00/month
- Data transfer: Usually included in bundle

## Security Notes
- Change default SSH keys
- Consider using HTTPS with SSL certificate
- Restrict API access if needed
- Regular security updates