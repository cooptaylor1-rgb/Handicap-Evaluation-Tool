#!/bin/bash

# Script to run the Golf Scoring Probability Engine for mobile access
# This will display the URLs you can use to access the app from your iPhone

echo "======================================"
echo "Golf Scoring Probability Engine"
echo "Mobile Access Setup"
echo "======================================"
echo ""

# Get local IP address
LOCAL_IP=$(hostname -I | awk '{print $1}')

if [ -z "$LOCAL_IP" ]; then
    echo "❌ Could not detect local IP address"
    exit 1
fi

echo "🖥️  Server will run on: http://$LOCAL_IP:8000"
echo ""
echo "📱 To access from your iPhone:"
echo "   1. Make sure your iPhone is on the SAME Wi-Fi network"
echo "   2. Open Safari on your iPhone"
echo "   3. Navigate to: http://$LOCAL_IP:8000"
echo "   4. (Optional) Tap Share → Add to Home Screen for quick access"
echo ""
echo "🔧 Starting server..."
echo ""

# Start the server
cd "$(dirname "$0")"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
