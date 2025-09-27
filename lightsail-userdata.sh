#!/bin/bash

# AWS Lightsail User Data Script
# This script runs when the instance first starts

# Update system
apt-get update -y
apt-get upgrade -y

# Install Python 3.9 and pip
apt-get install -y python3.9 python3.9-venv python3-pip git

# Install system dependencies for geospatial libraries
apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    libspatialindex-dev \
    build-essential \
    python3.9-dev

# Create app directory
mkdir -p /opt/hkspecies
cd /opt/hkspecies

# Clone or copy application files (you'll need to upload these)
# For now, we'll create the basic structure

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install Python dependencies
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pandas==2.1.3
geopandas==0.14.1
numpy==1.24.3
torch==2.1.1
psutil==5.9.6
python-multipart==0.0.6
pyogrio==0.7.2
rasterio==1.3.9
rasterstats==0.19.0
contextily==1.4.0
shapely==2.0.2
matplotlib==3.8.2
EOF

pip install -r requirements.txt

# Create a simple startup script
cat > start.sh << 'EOF'
#!/bin/bash
cd /opt/hkspecies
source venv/bin/activate
python app.py
EOF

chmod +x start.sh

# Create systemd service
cat > /etc/systemd/system/hkspecies.service << 'EOF'
[Unit]
Description=Hong Kong Species API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/hkspecies
ExecStart=/opt/hkspecies/start.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service (will fail initially until files are uploaded)
systemctl daemon-reload
systemctl enable hkspecies

# Create upload instructions
cat > /home/ubuntu/UPLOAD_INSTRUCTIONS.txt << 'EOF'
Hong Kong Species API - Upload Instructions
==========================================

1. Upload your application files to /opt/hkspecies/
   Required files:
   - app.py (main FastAPI application)
   - species_api.py (if using this instead of app.py)
   - species_inference.py (prediction model)
   - api_models.py (data models)
   - processed/ directory (with all processed data files)
   - boundaries/ directory (with shapefiles)
   - hk.tif (Hong Kong map file)
   - frontend.html (web interface)

2. Set correct permissions:
   sudo chown -R ubuntu:ubuntu /opt/hkspecies/
   sudo chmod +x /opt/hkspecies/start.sh

3. Start the service:
   sudo systemctl start hkspecies
   sudo systemctl status hkspecies

4. Check logs:
   sudo journalctl -u hkspecies -f

5. Test the API:
   curl http://localhost:8000/health

Upload files using SCP:
scp -i your-key.pem -r /local/path/* ubuntu@YOUR_IP:/opt/hkspecies/

Or use rsync:
rsync -avz -e "ssh -i your-key.pem" /local/path/ ubuntu@YOUR_IP:/opt/hkspecies/
EOF

chown ubuntu:ubuntu /home/ubuntu/UPLOAD_INSTRUCTIONS.txt

echo "✅ Server setup complete. Upload your application files to start the service."