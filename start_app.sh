#!/bin/bash

# Simple script to start the app directly on port 8000
# Use this if systemd service doesn't work

cd /var/www/hkspecies

echo "Starting HK Species app on port 8000..."
python3.11 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload