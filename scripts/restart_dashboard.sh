#!/usr/bin/env bash
# Restart Unified Memory Dashboard reliably from VS Code task
# - Stops any existing instance
# - Starts a fresh background instance with auto-start
# - Waits briefly for server readiness
# - Opens browser when ready

# Stop previous instance (ignore errors if not running)
pkill -f unified_memory_dashboard.py >/dev/null 2>&1 || true

# Ensure log directory exists
mkdir -p "$HOME/.ClipboardMonitor"

# Start new instance in background
nohup python3 unified_memory_dashboard.py --auto-start > "$HOME/.ClipboardMonitor/dashboard.out" 2>&1 &

# Wait up to ~6 seconds (30 x 0.2s) for server readiness
for i in $(seq 1 30); do
  sleep 0.2
  if curl -fsS http://localhost:8001/ >/dev/null; then
    # Open in default browser
    open http://localhost:8001 >/dev/null 2>&1 || true
    echo "Dashboard (re)started"
    exit 0
  fi
done

echo "Dashboard started but not reachable yet. Check $HOME/.ClipboardMonitor/dashboard.out"
exit 0

