#!/bin/bash

# Startup script using cached predictions from GitHub
echo "🚀 Starting HK Species app with cached predictions..."

cd ~/hkspecies

# Check if predictions cache exists
if [ -d "predictions_cache" ]; then
    echo "✅ Predictions cache found, starting server..."
else
    echo "❌ No predictions cache found! Make sure to pull from GitHub with cache."
    exit 1
fi

# Start the app directly
echo "🌐 Starting FastAPI server..."
python3.11 -m uvicorn app:app --host 0.0.0.0 --port 8000