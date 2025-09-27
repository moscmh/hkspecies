#!/bin/bash
# Check application status

echo "🔍 Checking Hong Kong Species API Status..."
echo "=" * 50

# Check if process is running
echo "📋 Process Status:"
ps aux | grep python3.11 | grep -v grep

echo ""
echo "🌐 API Health Check:"
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "📊 API Summary:"
curl -s http://localhost:8000/api/summary | python3 -m json.tool

echo ""
echo "🔗 Access URLs:"
echo "   Frontend: http://3.25.93.9:8000"
echo "   Health:   http://3.25.93.9:8000/health"
echo "   API:      http://3.25.93.9:8000/api/summary"

echo ""
echo "📝 Recent Logs:"
tail -n 10 app.log