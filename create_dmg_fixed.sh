#!/bin/bash
set -e

# Fixed DMG Creation Script for Clipboard Monitor
# This version handles file copying issues better

# --- Configuration & Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_NAME="Clipboard Monitor"
APP_BUNDLE="Clipboard Monitor.app"
DMG_NAME="ClipboardMonitor-1.0"
DMG_TEMP_NAME="temp_${DMG_NAME}"
VOLUME_NAME="Clipboard Monitor"
DMG_SIZE="100m"

print_status() {
    echo -e "${BLUE}📦 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Clean up any existing DMGs and mounted volumes
cleanup() {
    print_status "Cleaning up..."
    
    # Unmount any existing volumes
    hdiutil detach "/Volumes/${VOLUME_NAME}" 2>/dev/null || true
    hdiutil detach "/Volumes/Clipboard Monitor 1" 2>/dev/null || true
    
    # Remove existing DMG files
    rm -f "${DMG_NAME}.dmg"
    rm -f "${DMG_TEMP_NAME}.dmg"
    
    print_success "Cleanup completed"
}

# Create DMG
create_dmg() {
    print_status "Creating DMG with fixed KeepAlive settings..."
    
    # Check if app bundle exists
    if [ ! -d "$APP_BUNDLE" ]; then
        print_error "App bundle '$APP_BUNDLE' not found"
        exit 1
    fi
    
    # Verify KeepAlive is set to false
    if grep -A 1 "KeepAlive" "$APP_BUNDLE/Contents/Resources/com.clipboardmonitor.plist" | grep -q "<true/>"; then
        print_error "KeepAlive is still set to true in main plist file!"
        exit 1
    fi

    if grep -A 1 "KeepAlive" "$APP_BUNDLE/Contents/Resources/com.clipboardmonitor.menubar.plist" | grep -q "<true/>"; then
        print_error "KeepAlive is still set to true in menubar plist file!"
        exit 1
    fi

    print_success "Verified: KeepAlive=false in plist files"
    
    # Create temporary directory for DMG contents
    TEMP_DIR=$(mktemp -d)
    print_status "Using temporary directory: $TEMP_DIR"
    
    # Copy app bundle to temp directory
    print_status "Copying application bundle..."
    cp -R "$APP_BUNDLE" "$TEMP_DIR/"
    
    # Copy install scripts
    if [ -f "install.sh" ]; then
        cp "install.sh" "$TEMP_DIR/"
        chmod +x "$TEMP_DIR/install.sh"
    fi
    
    if [ -f "uninstall.sh" ]; then
        cp "uninstall.sh" "$TEMP_DIR/"
        chmod +x "$TEMP_DIR/uninstall.sh"
    fi
    
    if [ -f "emergency_stop_spawning.sh" ]; then
        cp "emergency_stop_spawning.sh" "$TEMP_DIR/"
        chmod +x "$TEMP_DIR/emergency_stop_spawning.sh"
    fi

    # Copy plist files for manual installation
    if [ -f "plist_files/com.clipboardmonitor.plist" ]; then
        cp "plist_files/com.clipboardmonitor.plist" "$TEMP_DIR/"
    fi

    if [ -f "plist_files/com.clipboardmonitor.menubar.plist" ]; then
        cp "plist_files/com.clipboardmonitor.menubar.plist" "$TEMP_DIR/"
    fi

    # Create Applications symlink
    ln -s /Applications "$TEMP_DIR/Applications"
    
    # Create README
    cat > "$TEMP_DIR/README.txt" << 'EOF'
Clipboard Monitor - Development Version
======================================

This version has the critical KeepAlive bug fixed to prevent multiple menu bar app spawning.

INSTALLATION:
1. Drag "Clipboard Monitor.app" to the Applications folder
2. Run the install.sh script to set up background services
3. MANUAL STEP: Copy the plist files to ~/Library/LaunchAgents/ when prompted
   - com.clipboardmonitor.plist
   - com.clipboardmonitor.menubar.plist
4. The app will appear in your menu bar

NOTE: Manual plist installation is required due to SentinelOne security software.

EMERGENCY STOP:
If you experience multiple spawning, immediately run:
./emergency_stop_spawning.sh

UNINSTALLATION:
Run the uninstall.sh script to completely remove the application.

Key Fix: KeepAlive=false (was true, causing infinite respawning)

For support: https://github.com/omairaslam/Clipboard-Monitor
EOF
    
    # Create DMG from directory
    print_status "Creating DMG from directory..."
    hdiutil create -volname "$VOLUME_NAME" -srcfolder "$TEMP_DIR" -ov -format UDZO "$DMG_NAME.dmg"
    
    # Clean up temp directory
    rm -rf "$TEMP_DIR"
    
    print_success "DMG created: $DMG_NAME.dmg"
}

# Verify DMG contents
verify_dmg() {
    print_status "Verifying DMG contents..."
    
    # Mount DMG
    hdiutil attach "$DMG_NAME.dmg"
    
    # Check KeepAlive setting in mounted DMG
    if grep -q "<false/>" "/Volumes/${VOLUME_NAME}/Clipboard Monitor.app/Contents/Resources/com.clipboardmonitor.plist"; then
        print_success "✅ Verified: KeepAlive=false in DMG"
    else
        print_error "❌ KeepAlive setting incorrect in DMG"
        hdiutil detach "/Volumes/${VOLUME_NAME}"
        exit 1
    fi
    
    # List contents
    echo ""
    echo "DMG Contents:"
    ls -la "/Volumes/${VOLUME_NAME}/"
    
    # Unmount
    hdiutil detach "/Volumes/${VOLUME_NAME}"
    
    print_success "DMG verification completed"
}

# Main execution
main() {
    echo "🚀 Creating FIXED Clipboard Monitor DMG"
    echo "========================================"
    
    cleanup
    create_dmg
    verify_dmg
    
    echo ""
    echo "========================================"
    print_success "FIXED DMG creation completed successfully!"
    echo ""
    echo "📱 DMG file: $DMG_NAME.dmg"
    echo "📁 Size: $(du -sh "$DMG_NAME.dmg" | cut -f1)"
    echo ""
    echo "🔧 Key Fix: KeepAlive=false (prevents multiple spawning)"
    echo "🚀 Ready for distribution and testing!"
}

main "$@"
