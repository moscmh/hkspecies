# Deployment with Cached Predictions

## Local Setup (Generate Cache)
```bash
# Generate predictions cache locally
python3.11 precompute_predictions.py

# Commit cache to GitHub
git add predictions_cache/
git commit -m "Add pre-computed predictions cache"
git push origin main
```

## Lightsail Deployment
```bash
# SSH into instance
ssh -i ~/.ssh/LightsailDefaultKey-us-east-1.pem ubuntu@YOUR_IP

# Pull latest with cache
cd ~/hkspecies
git pull origin main

# Verify cache exists
ls -la predictions_cache/

# Start with cached predictions
chmod +x startup_cached.sh
./startup_cached.sh
```

## Service Update
```bash
# Update systemd service to use cached startup
sudo tee /etc/systemd/system/hkspecies.service > /dev/null <<EOF
[Unit]
Description=HK Species FastAPI App
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/hkspecies
ExecStart=/home/ubuntu/hkspecies/startup_cached.sh
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl restart hkspecies
```

## Benefits
- ⚡ Instant predictions (no training)
- 💾 No memory pressure
- 🚀 Fast startup
- 📦 Predictions included in repo