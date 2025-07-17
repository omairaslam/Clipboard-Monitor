#!/bin/bash

# Test Menu Bar Spawning Issue
# This script helps isolate exactly what's causing multiple menu bar instances

echo "🧪 Testing Menu Bar Spawning Issue"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

MENUBAR_EXECUTABLE="/Applications/Clipboard Monitor.app/Contents/MacOS/ClipboardMonitorMenuBar"
MENUBAR_PLIST="$HOME/Library/LaunchAgents/com.clipboardmonitor.menubar.plist"

# Step 1: Clean slate
print_status "Starting with clean slate..."
pkill -f ClipboardMonitor 2>/dev/null || true
launchctl unload "$MENUBAR_PLIST" 2>/dev/null || true
sleep 2
print_success "Clean slate ready"
echo ""

# Step 2: Test direct execution
print_status "Test 1: Running executable directly..."
echo "Command: $MENUBAR_EXECUTABLE"
echo "Starting executable in background..."

# Run the executable directly and monitor
"$MENUBAR_EXECUTABLE" &
DIRECT_PID=$!
echo "Started with PID: $DIRECT_PID"

# Monitor for 10 seconds
for i in {1..10}; do
    sleep 1
    PROCESS_COUNT=$(ps aux | grep -c "ClipboardMonitorMenuBar" | grep -v grep || echo "0")
    echo "Second $i: $PROCESS_COUNT ClipboardMonitorMenuBar processes"
    
    if [ "$PROCESS_COUNT" -gt 1 ]; then
        print_error "Multiple instances detected during direct execution!"
        ps aux | grep "ClipboardMonitorMenuBar" | grep -v grep
        break
    fi
done

# Kill the direct execution
kill $DIRECT_PID 2>/dev/null || true
pkill -f ClipboardMonitor 2>/dev/null || true
sleep 2
echo ""

# Step 3: Test LaunchAgent execution
print_status "Test 2: Running via LaunchAgent..."
echo "Command: launchctl load $MENUBAR_PLIST"

# Monitor before loading
echo "Before loading LaunchAgent:"
ps aux | grep "ClipboardMonitor" | grep -v grep || echo "No processes"

# Load the LaunchAgent
echo "Loading LaunchAgent..."
launchctl load "$MENUBAR_PLIST"

# Monitor immediately after loading
echo "Immediately after loading:"
ps aux | grep "ClipboardMonitor" | grep -v grep || echo "No processes"

# Monitor for 10 seconds
for i in {1..10}; do
    sleep 1
    PROCESS_COUNT=$(ps aux | grep "ClipboardMonitorMenuBar" | grep -v grep | wc -l | tr -d ' ')
    echo "Second $i: $PROCESS_COUNT ClipboardMonitorMenuBar processes"
    
    if [ "$PROCESS_COUNT" -gt 1 ]; then
        print_error "Multiple instances detected via LaunchAgent!"
        echo "Process details:"
        ps aux | grep "ClipboardMonitorMenuBar" | grep -v grep
        echo ""
        
        # Check if they have different PIDs and parent PIDs
        echo "Process tree:"
        ps -eo pid,ppid,comm,args | grep ClipboardMonitor | grep -v grep
        break
    fi
done

# Step 4: Check for crash logs
print_status "Checking for crash logs..."
RECENT_CRASHES=$(find ~/Library/Logs/DiagnosticReports -name "*ClipboardMonitor*" -mtime -1 2>/dev/null)
if [ -n "$RECENT_CRASHES" ]; then
    print_warning "Recent crash logs found:"
    ls -la $RECENT_CRASHES
    echo ""
    echo "Latest crash excerpt:"
    head -30 $(echo "$RECENT_CRASHES" | head -1) 2>/dev/null
else
    print_success "No recent crash logs"
fi
echo ""

# Step 5: Check LaunchAgent status
print_status "Checking LaunchAgent status..."
launchctl list | grep clipboard || echo "No clipboard services loaded"
echo ""

# Step 6: Check log files
print_status "Checking log files..."
LOG_OUT="/Users/omair.aslam/Library/Logs/ClipboardMonitorMenuBar.out.log"
LOG_ERR="/Users/omair.aslam/Library/Logs/ClipboardMonitorMenuBar.err.log"

if [ -f "$LOG_OUT" ]; then
    echo "Output log (last 10 lines):"
    tail -10 "$LOG_OUT"
else
    echo "No output log found"
fi

if [ -f "$LOG_ERR" ]; then
    echo "Error log (last 10 lines):"
    tail -10 "$LOG_ERR"
else
    echo "No error log found"
fi
echo ""

# Cleanup
print_status "Cleaning up..."
launchctl unload "$MENUBAR_PLIST" 2>/dev/null || true
pkill -f ClipboardMonitor 2>/dev/null || true

echo ""
print_warning "ANALYSIS COMPLETE"
echo "If multiple instances appeared during LaunchAgent loading but not direct execution,"
echo "the issue is likely in the LaunchAgent configuration or app's response to being"
echo "launched by launchd vs. direct execution."
echo ""

echo "Press any key to continue..."
read -n 1 -s
