#!/bin/bash

# Quick start script for Golf Calculator - iPhone Access
# Run this script to start the server and get connection info

clear

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Golf Scoring Probability Calculator  ║${NC}"
echo -e "${GREEN}║          iPhone Access Mode            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

if [ -z "$LOCAL_IP" ]; then
    echo -e "${YELLOW}⚠️  Could not detect local IP address${NC}"
    echo "   Try running: ip addr show | grep 'inet '"
    exit 1
fi

echo -e "${BLUE}🌐 Your Local IP: ${NC}$LOCAL_IP"
echo -e "${BLUE}🔌 Port: ${NC}8000"
echo ""
echo -e "${GREEN}📱 iPhone Connection URL:${NC}"
echo ""
echo -e "   ${YELLOW}http://$LOCAL_IP:8000${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✓ Mobile optimizations enabled"
echo "✓ Touch-friendly interface"
echo "✓ Form data persistence"
echo "✓ Add to Home Screen support"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Steps:"
echo "   1. Connect iPhone to SAME Wi-Fi network"
echo "   2. Open Safari on iPhone"
echo "   3. Enter: http://$LOCAL_IP:8000"
echo "   4. Bookmark or Add to Home Screen"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Starting server..."
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
