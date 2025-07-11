#!/bin/bash
# Safe Menu Bar App Restart Script
# Ensures clean shutdown before starting new instance

echo "🔄 Safe Menu Bar App Restart"
echo "============================"

# Step 1: Find and stop all menu bar processes
echo "1. Stopping existing menu bar processes..."
PIDS=$(ps aux | grep menu_bar_app.py | grep -v grep | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "   Found processes: $PIDS"
    for PID in $PIDS; do
        echo "   Stopping PID $PID..."
        kill $PID
    done
    
    # Wait for graceful shutdown
    echo "   Waiting for graceful shutdown..."
    sleep 3
    
    # Force kill if still running
    REMAINING=$(ps aux | grep menu_bar_app.py | grep -v grep | awk '{print $2}')
    if [ -n "$REMAINING" ]; then
        echo "   Force stopping remaining processes: $REMAINING"
        for PID in $REMAINING; do
            kill -9 $PID
        done
    fi
else
    echo "   No existing processes found"
fi

# Step 2: Wait for cleanup
echo "2. Waiting for system cleanup..."
sleep 2

# Step 3: Verify no processes remain
FINAL_CHECK=$(ps aux | grep menu_bar_app.py | grep -v grep)
if [ -n "$FINAL_CHECK" ]; then
    echo "   ⚠️  Warning: Some processes may still be running"
    echo "$FINAL_CHECK"
else
    echo "   ✅ All processes stopped"
fi

# Step 4: Start fresh instance
echo "3. Starting fresh menu bar app..."
cd "$(dirname "$0")"
python3 menu_bar_app.py &
NEW_PID=$!

# Step 5: Verify startup
echo "4. Verifying startup..."
sleep 3

if ps -p $NEW_PID > /dev/null; then
    MEMORY=$(ps -o rss= -p $NEW_PID | awk '{print $1/1024}')
    echo "   ✅ Menu bar app started successfully"
    echo "   PID: $NEW_PID"
    echo "   Memory: ${MEMORY}MB"
    
    if (( $(echo "$MEMORY > 100" | bc -l) )); then
        echo "   ⚠️  Memory usage seems high for fresh process"
    else
        echo "   ✅ Memory usage looks good"
    fi
else
    echo "   ❌ Failed to start menu bar app"
    exit 1
fi

echo ""
echo "✅ Safe restart complete!"
echo "   Check your menu bar for a single clipboard monitor icon"
