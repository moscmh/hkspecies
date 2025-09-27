#!/bin/bash
# Quick restart script

echo "🔄 Restarting Hong Kong Species API..."

# Kill existing process
pkill -f "python.*app.py"
sleep 2

# Start new process
nohup python3.11 app.py > app.log 2>&1 &

echo "✅ Application restarted!"
echo "📋 Check status: ps aux | grep python"
echo "📋 View logs: tail -f app.log"
echo "🌐 Access: http://3.25.93.9:8000"