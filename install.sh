#!/bin/bash

# Define paths
APP_NAME="Clipboard Monitor"
INSTALL_DIR="$HOME/Applications/$APP_NAME.app"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$HOME/Library/Logs"
PLIST_BACKGROUND="com.omairaslam.clipboardmonitor.plist"
PLIST_MENUBAR="com.omairaslam.clipboardmonitor.menubar.plist"

# Create directories
mkdir -p "$LAUNCH_AGENTS_DIR"
mkdir -p "$LOG_DIR"

# Unload existing services
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" 2>/dev/null
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" 2>/dev/null

# Generate background service plist
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

# Load services
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR"

echo "Installation complete."
echo "The application has been installed to $INSTALL_DIR"
echo "Services have been loaded. You can manage them with launchctl."