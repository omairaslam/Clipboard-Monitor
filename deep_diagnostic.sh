#!/bin/bash

# Deep Diagnostic for Multiple ClipboardMonitor Spawning
# This investigates the REAL cause of multiple instances

echo "🔬 Deep ClipboardMonitor Spawning Analysis"
echo "=========================================="
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

# Step 1: Real-time process monitoring
print_status "Monitoring ClipboardMonitor processes in real-time..."
echo "Current processes:"
ps aux | grep -i "ClipboardMonitor\|MenuBar" | grep -v grep | grep -v diagnostic
echo ""

# Step 2: Check what's actually launching the processes
print_status "Checking what's launching ClipboardMonitor processes..."
echo ""

# Check launchctl services
echo "LaunchAgent services:"
launchctl list | grep -i clipboard || echo "No clipboard services in launchctl"
echo ""

# Check if processes are being launched by launchd
echo "Checking parent processes of ClipboardMonitor:"
ps -eo pid,ppid,comm,args | grep -i clipboard | grep -v grep | grep -v diagnostic
echo ""

# Step 3: Check the actual executables being run
print_status "Analyzing executable paths and arguments..."
ps aux | grep -i "ClipboardMonitor\|MenuBar" | grep -v grep | grep -v diagnostic | while read line; do
    echo "Process: $line"
    PID=$(echo "$line" | awk '{print $2}')
    if [ -n "$PID" ]; then
        echo "  Command line: $(ps -p $PID -o args= 2>/dev/null || echo 'Process not found')"
        echo "  Parent PID: $(ps -p $PID -o ppid= 2>/dev/null || echo 'Unknown')"
    fi
    echo ""
done

# Step 4: Check for crash logs
print_status "Checking for crash logs..."
CRASH_LOGS=$(find ~/Library/Logs/DiagnosticReports -name "*ClipboardMonitor*" -mtime -1 2>/dev/null | head -5)
if [ -n "$CRASH_LOGS" ]; then
    print_warning "Recent crash logs found:"
    echo "$CRASH_LOGS"
    echo ""
    echo "Latest crash log excerpt:"
    head -20 $(echo "$CRASH_LOGS" | head -1) 2>/dev/null || echo "Could not read crash log"
else
    print_success "No recent crash logs found"
fi
echo ""

# Step 5: Check application bundle for multiple executables
print_status "Checking application bundle structure..."
APP_PATH="/Applications/Clipboard Monitor.app"
if [ -d "$APP_PATH" ]; then
    echo "Main executable:"
    ls -la "$APP_PATH/Contents/MacOS/"
    echo ""
    
    echo "Services directory:"
    if [ -d "$APP_PATH/Contents/Resources/Services" ]; then
        find "$APP_PATH/Contents/Resources/Services" -name "*.app" -type d
        echo ""
        
        # Check each service app
        find "$APP_PATH/Contents/Resources/Services" -name "*.app" -type d | while read service_app; do
            echo "Service app: $service_app"
            if [ -d "$service_app/Contents/MacOS" ]; then
                ls -la "$service_app/Contents/MacOS/"
            fi
            echo ""
        done
    else
        echo "No Services directory found"
    fi
else
    print_error "Application not found: $APP_PATH"
fi
echo ""

# Step 6: Check for auto-restart mechanisms
print_status "Checking for auto-restart mechanisms..."

# Check if the app has internal restart logic
echo "Checking for restart-related strings in executables:"
if [ -f "$APP_PATH/Contents/MacOS/ClipboardMonitorMenuBar" ]; then
    strings "$APP_PATH/Contents/MacOS/ClipboardMonitorMenuBar" | grep -i -E "(restart|spawn|launch|fork|exec)" | head -5 || echo "No restart-related strings found"
fi
echo ""

# Step 7: Check system logs for launch patterns
print_status "Checking system logs for launch patterns..."
echo "Recent system log entries for ClipboardMonitor:"
log show --predicate 'process CONTAINS "ClipboardMonitor"' --last 10m --info 2>/dev/null | tail -10 || echo "No recent log entries"
echo ""

# Step 8: Monitor launch sequence
print_status "Monitoring launch sequence..."
echo "Starting fresh monitoring - kill all processes first..."
pkill -f ClipboardMonitor 2>/dev/null || true
sleep 2

echo "Current state after kill:"
ps aux | grep -i "ClipboardMonitor\|MenuBar" | grep -v grep | grep -v diagnostic || echo "No processes running"
echo ""

echo "Now manually trigger the services and watch what happens..."
echo "Run this in another terminal:"
echo "  launchctl load ~/Library/LaunchAgents/com.clipboardmonitor.plist"
echo "  launchctl load ~/Library/LaunchAgents/com.clipboardmonitor.menubar.plist"
echo ""
echo "Then check processes again:"
echo "  ps aux | grep ClipboardMonitor"
echo ""

print_warning "HYPOTHESIS: The issue might be:"
echo "1. App crashes immediately and gets restarted by something else"
echo "2. App launches multiple instances internally"
echo "3. LaunchAgent is being loaded multiple times"
echo "4. App has internal spawning logic"
echo "5. System is detecting crashes and auto-restarting"
echo ""

echo "Press any key to continue..."
read -n 1 -s
