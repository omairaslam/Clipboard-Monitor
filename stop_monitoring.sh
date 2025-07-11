#!/bin/bash
# Stop memory monitoring
echo "🛑 Stopping Memory Monitoring System..."
cd "$(dirname "$0")"

if [ -f .monitoring_pids ]; then
    PIDS=$(cat .monitoring_pids)
    for PID in $PIDS; do
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping process $PID..."
            kill $PID
        fi
    done
    rm .monitoring_pids
    echo "✅ Memory monitoring stopped"
else
    echo "⚠️  No PID file found - manually kill processes if needed"
fi
