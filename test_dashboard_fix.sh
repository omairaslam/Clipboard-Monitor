#!/bin/bash

# Test Dashboard Fix
# This script tests if the unified dashboard fixes work correctly

echo "🧪 Testing Dashboard Fixes"
echo "=========================="
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

# Step 1: Check current state
print_status "Checking current ClipboardMonitor state..."
clipboard_processes=$(ps aux | grep -i "ClipboardMonitor" | grep -v grep | wc -l | tr -d ' ')
echo "Current ClipboardMonitor processes: $clipboard_processes"

if [ "$clipboard_processes" -eq 0 ]; then
    print_warning "No ClipboardMonitor processes running. Please start the services first."
    echo "Run: launchctl load ~/Library/LaunchAgents/com.clipboardmonitor.plist"
    echo "Run: launchctl load ~/Library/LaunchAgents/com.clipboardmonitor.menubar.plist"
    exit 1
fi

# Step 2: Test dashboard script directly
print_status "Testing dashboard script directly..."
DASHBOARD_SCRIPT="/Applications/Clipboard Monitor.app/Contents/MacOS/unified_memory_dashboard.py"

if [ ! -f "$DASHBOARD_SCRIPT" ]; then
    # Try alternative paths
    DASHBOARD_SCRIPT="/Applications/Clipboard Monitor.app/Contents/Resources/unified_memory_dashboard.py"
fi

if [ ! -f "$DASHBOARD_SCRIPT" ]; then
    # Try in current directory
    DASHBOARD_SCRIPT="./unified_memory_dashboard.py"
fi

if [ -f "$DASHBOARD_SCRIPT" ]; then
    print_success "Found dashboard script: $DASHBOARD_SCRIPT"
    
    # Test if script starts without errors
    echo "Testing dashboard script startup..."
    timeout 5 python3 "$DASHBOARD_SCRIPT" --auto-start &
    DASHBOARD_PID=$!
    sleep 3
    
    if kill -0 $DASHBOARD_PID 2>/dev/null; then
        print_success "Dashboard script started successfully"
        kill $DASHBOARD_PID 2>/dev/null
    else
        print_error "Dashboard script failed to start or exited immediately"
    fi
else
    print_error "Dashboard script not found"
fi

# Step 3: Check for multiple instances after dashboard test
print_status "Checking for multiple instances after dashboard test..."
clipboard_processes_after=$(ps aux | grep -i "ClipboardMonitor" | grep -v grep | wc -l | tr -d ' ')
echo "ClipboardMonitor processes after test: $clipboard_processes_after"

if [ "$clipboard_processes_after" -gt "$clipboard_processes" ]; then
    print_error "Additional ClipboardMonitor processes spawned during test!"
    echo "Before: $clipboard_processes, After: $clipboard_processes_after"
    echo "New processes:"
    ps aux | grep -i "ClipboardMonitor" | grep -v grep
else
    print_success "No additional processes spawned"
fi

# Step 4: Test port availability
print_status "Testing port 8001 availability..."
if lsof -i :8001 > /dev/null 2>&1; then
    print_warning "Port 8001 is already in use"
    echo "Process using port 8001:"
    lsof -i :8001
else
    print_success "Port 8001 is available"
fi

echo ""
print_status "Test Summary:"
echo "• Dashboard script found: $([ -f "$DASHBOARD_SCRIPT" ] && echo "✅ Yes" || echo "❌ No")"
echo "• No additional processes spawned: $([ "$clipboard_processes_after" -eq "$clipboard_processes" ] && echo "✅ Yes" || echo "❌ No")"
echo "• Port 8001 available: $(lsof -i :8001 > /dev/null 2>&1 && echo "⚠️  In use" || echo "✅ Available")"

echo ""
echo "Next steps:"
echo "1. Try launching the unified dashboard from the menu bar app"
echo "2. Check if browser opens to localhost:8001"
echo "3. Verify no additional menu bar instances spawn"
echo "4. Check if dashboard website loads properly"
