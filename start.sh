#!/bin/bash
# Launch AIdeate Workshop with audience voting
# Serves files via server.py (HTTP + REST API for interactive voting)
cd "$(dirname "$0")"
PORT=${1:-8765}

# Detect LAN IP
LAN_IP=$(python3 -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()" 2>/dev/null || echo "localhost")

echo ""
echo "  🚀 AIdeate Workshop"
echo "  ══════════════════════════════════════"
echo "  Presenter:  http://localhost:$PORT/index.html"
echo "  Join URL:   http://$LAN_IP:$PORT/join.html"
echo "  ──────────────────────────────────────"
echo "  📱 Share the join URL or QR code so"
echo "     participants can vote from their phones."
echo "  ══════════════════════════════════════"
echo "  Press Ctrl+C to stop"
echo ""

# Open presenter in browser
open "http://localhost:$PORT/index.html" 2>/dev/null || xdg-open "http://localhost:$PORT/index.html" 2>/dev/null || true

# Launch server (with REST API for audience voting)
python3 server.py $PORT
