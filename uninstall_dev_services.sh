#!/bin/bash

# Uninstall Development Services Script
# This removes ClipboardMonitor development services

set -e

# Source the shared configuration
source "$(dirname "$0")/_config.sh"

echo "🗑️  Uninstalling ClipboardMonitor Development Services..."

# Stop and unload development services (both from LaunchAgents)
echo "🛑 Stopping development services..."
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" 2>/dev/null || true
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" 2>/dev/null || true

# Remove plist files
echo "📦 Removing plist files..."
rm -f "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"
rm -f "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR"

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
