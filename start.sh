#!/bin/bash
# Launch AIdeate Workshop locally
# Serves files via HTTP (required for BroadcastChannel + iframes)
cd "$(dirname "$0")"
PORT=${1:-8765}
echo "🚀 AIdeate Workshop starting on http://localhost:$PORT"
echo "   Control Panel: http://localhost:$PORT/workshop-control.html"
echo "   Presenter:     http://localhost:$PORT/workshop-presenter.html"
echo ""
echo "   Press Ctrl+C to stop"
echo ""
open "http://localhost:$PORT/workshop-control.html"
open "http://localhost:$PORT/workshop-presenter.html"
python3 -m http.server $PORT
