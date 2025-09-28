#!/bin/bash

# Startup script to pre-compute all predictions
echo "🚀 Starting HK Species app with prediction pre-computation..."

cd ~/hkspecies

# Run pre-computation
echo "📊 Pre-computing all species predictions..."
python3.11 precompute_predictions.py

# Start the app
echo "🌐 Starting FastAPI server..."
python3.11 -m uvicorn app:app --host 0.0.0.0 --port 8000