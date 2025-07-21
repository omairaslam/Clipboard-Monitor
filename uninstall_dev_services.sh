#!/bin/bash

# Uninstall Development Services Script
# This removes ClipboardMonitor development services

set -e

echo "🗑️  Uninstalling ClipboardMonitor Development Services..."

# Stop and unload development services (both from LaunchAgents)
echo "🛑 Stopping development services..."
launchctl unload ~/Library/LaunchAgents/com.clipboardmonitor.service.dev.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/com.clipboardmonitor.menubar.dev.plist 2>/dev/null || true

# Remove plist files
echo "📦 Removing plist files..."
rm -f ~/Library/LaunchAgents/com.clipboardmonitor.service.dev.plist
rm -f ~/Library/LaunchAgents/com.clipboardmonitor.menubar.dev.plist

# Kill any remaining Python processes
echo "🔪 Killing any remaining Python processes..."
pkill -f "main.py" 2>/dev/null || true
pkill -f "menu_bar_app.py" 2>/dev/null || true

# Wait a moment
sleep 2

# Check if processes are still running
echo "🔍 Checking for remaining processes..."
REMAINING=$(ps aux | grep -E "(main\.py|menu_bar_app\.py)" | grep -v grep | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    echo "⚠️  Warning: Some processes may still be running:"
    ps aux | grep -E "(main\.py|menu_bar_app\.py)" | grep -v grep
else
    echo "✅ All processes stopped"
fi

echo "✅ Development services uninstallation complete!"
echo ""
echo "📋 You can now:"
echo "  1. Install production services with the PKG installer"
echo "  2. Or reinstall development services with: ./install_dev_services.sh"
