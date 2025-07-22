#!/bin/bash

# Install Development Services Script
# This installs ClipboardMonitor services that point to Python files for troubleshooting

set -e

# Source the shared configuration
source "$(dirname "$0")/_config.sh"

echo "🔧 Installing ClipboardMonitor Development Services..."

# Get the current directory (project root)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Project directory: $PROJECT_DIR"

# Stop and unload existing services if they exist (check both locations)
echo "🛑 Stopping existing services..."
# Stop production services
sudo launchctl unload /Library/LaunchDaemons/com.clipboardmonitor.service.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/com.clipboardmonitor.service.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/com.clipboardmonitor.menubar.plist 2>/dev/null || true

# Stop development services if they exist
sudo launchctl unload "/Library/LaunchDaemons/$PLIST_BACKGROUND" 2>/dev/null || true
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" 2>/dev/null || true
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" 2>/dev/null || true

# Update the plist files with the correct project path
echo "📝 Updating plist files with current project path..."

# Update service plist
sed "s|/Users/omair.aslam/Library/CloudStorage/OneDrive-TRGCustomerSolutions,Inc.dbaIBEXGlobalSolutions,aDelawareCorporation/Omair VS Code Workspaces/Clipboard Monitor|$PROJECT_DIR|g" \
    "$PROJECT_DIR/$PLIST_BACKGROUND" > "/tmp/$PLIST_BACKGROUND"

# Update menu bar plist
sed "s|/Users/omair.aslam/Library/CloudStorage/OneDrive-TRGCustomerSolutions,Inc.dbaIBEXGlobalSolutions,aDelawareCorporation/Omair VS Code Workspaces/Clipboard Monitor|$PROJECT_DIR|g" \
    "$PROJECT_DIR/$PLIST_MENUBAR" > "/tmp/$PLIST_MENUBAR"

# Install both services as user agents (as you've been developing)
echo "📦 Installing main service..."
mkdir -p ~/Library/LaunchAgents
cp "/tmp/$PLIST_BACKGROUND" "$LAUNCH_AGENTS_DIR/"
chmod 644 "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"

# Install menu bar plist (runs as user agent)
echo "📦 Installing menu bar app..."
cp "/tmp/$PLIST_MENUBAR" "$LAUNCH_AGENTS_DIR/"
chmod 644 "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR"

# Create log directory
echo "📁 Creating log directory..."
mkdir -p ~/Library/Logs

# Load and start services (both as user agents)
echo "🚀 Starting services..."
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR"

# Wait a moment for services to start
sleep 3

# Check service status
echo "📊 Checking service status..."
echo "Main Service:"
launchctl list | grep "${PLIST_BACKGROUND%.plist}" || echo "  ❌ Not running"

echo "Menu Bar App:"
launchctl list | grep "${PLIST_MENUBAR%.plist}" || echo "  ❌ Not running"

# Show running processes
echo "🔍 ClipboardMonitor processes:"
ps aux | grep -E "(main\.py|menu_bar_app\.py)" | grep -v grep || echo "  ❌ No Python processes found"

echo "✅ Development services installation complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Check logs: tail -f ~/Library/Logs/ClipboardMonitor*.log"
echo "  2. Test unified dashboard: python3 unified_memory_dashboard.py --auto-start"
echo "  3. Uninstall with: ./uninstall_dev_services.sh"

# Clean up temp files
rm -f /tmp/com.clipboardmonitor.*.dev.plist
