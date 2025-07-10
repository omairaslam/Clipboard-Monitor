#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration & Colors ---
# Define colors for script output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Define application and system paths
APP_NAME="Clipboard Monitor.app"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$HOME/Library/Logs"
PLIST_BACKGROUND="com.omairaslam.clipboardmonitor.plist"
PLIST_MENUBAR="com.omairaslam.clipboardmonitor.menubar.plist"

# --- Uninstall Logic ---
# Check for the --uninstall flag to reverse the installation
if [ "$1" == "--uninstall" ]; then
    echo -e "${YELLOW}Uninstalling Clipboard Monitor services...${NC}"
    # Stop and unload the services, suppressing errors if they don't exist
    launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" 2>/dev/null || true
    launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" 2>/dev/null || true
    # Remove the configuration files
    rm -f "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"
    rm -f "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR"
    echo -e "${GREEN}✅ Services have been removed.${NC}"
    echo -e "${YELLOW}To complete the uninstall, please drag '$APP_NAME' from your Applications folder to the Trash.🗑️${NC}"
    exit 0
fi

# --- Main Installation ---
echo "This script will install the necessary background services for Clipboard Monitor."
# Ask for user confirmation before proceeding
read -p "Continue with installation? (y/n) " -n 1 -r
echo # Move to a new line

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 1
fi

# Verify application location
SYSTEM_APP_PATH="/Applications/$APP_NAME"
USER_APP_PATH="$HOME/Applications/$APP_NAME"
INSTALL_DIR=""

if [ -d "$SYSTEM_APP_PATH" ]; then
    INSTALL_DIR="$SYSTEM_APP_PATH"
elif [ -d "$USER_APP_PATH" ]; then
    INSTALL_DIR="$USER_APP_PATH"
else
    echo -e "${RED}Error: Could not find '$APP_NAME' in /Applications or ~/Applications.${NC}"
    echo "Please ensure the application is installed before running this script."
    exit 1
fi

echo -e "${GREEN}✅ Found application at: $INSTALL_DIR${NC}"

# Create necessary directories
echo "Ensuring necessary directories exist..."
mkdir -p "$LAUNCH_AGENTS_DIR"
mkdir -p "$LOG_DIR"

# Unload any existing services to ensure a clean installation
echo "Unloading any old services..."
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" 2>/dev/null || true
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" 2>/dev/null || true

# Generate background service plist
echo "Creating background service file..."
cat > "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.omairaslam.clipboardmonitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>$INSTALL_DIR/Contents/MacOS/python</string>
        <string>$INSTALL_DIR/Contents/Resources/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/ClipboardMonitor.out.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/ClipboardMonitor.err.log</string>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR/Contents/Resources/</string>
</dict>
</plist>
EOL

# Generate menubar service plist
echo "Creating menu bar service file..."
cat > "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.omairaslam.clipboardmonitor.menubar</string>
    <key>ProgramArguments</key>
    <array>
        <string>$INSTALL_DIR/Contents/MacOS/python</string>
        <string>$INSTALL_DIR/Contents/Resources/menu_bar_app.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/ClipboardMonitorMenuBar.out.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/ClipboardMonitorMenuBar.err.log</string>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR/Contents/Resources/</string>
</dict>
</plist>
EOL

# Load the new services
echo "Loading and starting services..."
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR"

# --- Final Summary ---
echo -e "\n${GREEN}✅ Success! Clipboard Monitor is now installed.${NC}"
echo "The following services have been configured:"
echo "  - Background Monitor: $LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"
echo "  - Menu Bar App:       $LAUNCH_AGENTS_DIR/$PLIST_MENUBAR"
echo ""
echo "To uninstall at any time, run this script again with the --uninstall flag."