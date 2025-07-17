#!/bin/bash

# Emergency Script to Stop Multiple Menu Bar App Spawning
# Run this immediately when you see multiple instances spawning

echo "🚨 EMERGENCY: Stopping Multiple Menu Bar App Spawning"
echo "=================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Immediately unload LaunchAgent services to stop respawning
echo "1. 🛑 Unloading LaunchAgent services to stop respawning..."
launchctl unload "$HOME/Library/LaunchAgents/com.clipboardmonitor.plist" 2>/dev/null || true
launchctl unload "$HOME/Library/LaunchAgents/com.clipboardmonitor.menubar.plist" 2>/dev/null || true
echo -e "${GREEN}✅ LaunchAgent services unloaded${NC}"

# Step 2: Kill all clipboard monitor processes aggressively
echo "2. 🔪 Killing all clipboard monitor processes..."

# Kill by process name patterns
pkill -f "ClipboardMonitor" 2>/dev/null || true
pkill -f "ClipboardMonitorMenuBar" 2>/dev/null || true
pkill -f "menu_bar_app.py" 2>/dev/null || true
pkill -f "main.py.*clipboard" 2>/dev/null || true
pkill -f "Clipboard Monitor" 2>/dev/null || true

# Wait a moment
sleep 2

# Force kill any stubborn processes
pkill -9 -f "ClipboardMonitor" 2>/dev/null || true
pkill -9 -f "ClipboardMonitorMenuBar" 2>/dev/null || true
pkill -9 -f "menu_bar_app.py" 2>/dev/null || true

echo -e "${GREEN}✅ All processes killed${NC}"

# Step 3: Verify no processes remain
echo "3. 🔍 Verifying no processes remain..."
REMAINING=$(ps aux | grep -i clipboard | grep -v grep | grep -v "emergency_stop")

if [ -n "$REMAINING" ]; then
    echo -e "${YELLOW}⚠️  Some processes may still be running:${NC}"
    echo "$REMAINING"
    echo ""
    echo -e "${YELLOW}If processes persist, you may need to restart your Mac${NC}"
else
    echo -e "${GREEN}✅ All clipboard monitor processes stopped${NC}"
fi

# Step 4: Remove plist files to prevent restart
echo "4. 🗑️  Removing plist files to prevent restart..."
rm -f "$HOME/Library/LaunchAgents/com.clipboardmonitor.plist" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/com.clipboardmonitor.menubar.plist" 2>/dev/null || true
echo -e "${GREEN}✅ Plist files removed${NC}"

echo ""
echo -e "${GREEN}🎉 Emergency stop completed!${NC}"
echo -e "${YELLOW}💡 The spawning should now be stopped.${NC}"
echo ""
echo "Next steps:"
echo "1. Wait a few seconds to ensure system stability"
echo "2. Use the fixed install script when ready to reinstall"
echo "3. Monitor Activity Monitor to ensure no processes restart"

echo ""
echo "Press any key to close..."
read -n 1 -s
