#!/bin/bash
# Start comprehensive memory monitoring
echo "🚀 Starting Memory Monitoring System..."
cd "$(dirname "$0")"

# Start long-term monitoring in background
python3 long_term_memory_monitor.py &
LONGTERM_PID=$!
echo "Long-term monitor started (PID: $LONGTERM_PID)"

# Start dashboard
python3 memory_monitoring_dashboard.py &
DASHBOARD_PID=$!
echo "Dashboard started (PID: $DASHBOARD_PID)"

echo "✅ Memory monitoring system started"
echo "   Dashboard: http://localhost:8002"
echo "   Long-term monitoring: Active"
echo ""
echo "To stop monitoring:"
echo "   kill $LONGTERM_PID $DASHBOARD_PID"
echo "   or run: ./stop_monitoring.sh"

# Save PIDs for stop script
echo "$LONGTERM_PID $DASHBOARD_PID" > .monitoring_pids
