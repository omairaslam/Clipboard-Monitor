#!/bin/bash
set -e

# PKG Installer Creation Script for Clipboard Monitor
# Creates native macOS installer package

# --- Configuration & Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_NAME="Clipboard Monitor"
APP_BUNDLE="Clipboard Monitor.app"
PKG_NAME="ClipboardMonitor-1.0.pkg"
IDENTIFIER="com.clipboardmonitor.installer"
VERSION="1.0.0"

# Print functions
print_status() {
    if [[ "$QUIET_MODE" != "true" ]]; then
        echo -e "${BLUE}📦 $1${NC}"
    fi
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Quiet mode specific functions
quiet_print_status() {
    if [[ "$QUIET_MODE" == "true" ]]; then
        echo -e "${BLUE}📦 $1${NC}"
    else
        print_status "$1"
    fi
}

# Create package structure
create_package_structure() {
    print_status "Creating package structure..."
    
    # Clean previous builds
    rm -rf pkg_root pkg_scripts pkg_resources
    
    # Create package root
    mkdir -p "pkg_root/Applications"
    mkdir -p "pkg_scripts"
    
    # Copy app bundle
    if [ ! -d "$APP_BUNDLE" ]; then
        print_error "App bundle '$APP_BUNDLE' not found!"
        exit 1
    fi
    
    cp -R "$APP_BUNDLE" "pkg_root/Applications/"
    print_success "App bundle copied to package structure"
}

# Create pre-install script
create_preinstall_script() {
    print_status "Creating pre-install script..."
    
    cat > "pkg_scripts/preinstall" << 'EOF'
#!/bin/bash
# Complete cleanup before installation

USER_HOME=$(eval echo ~$USER)
LAUNCH_AGENTS_DIR="$USER_HOME/Library/LaunchAgents"
LOG_DIR="$USER_HOME/Library/Logs"

# Stop and unload services
launchctl unload "$LAUNCH_AGENTS_DIR/com.clipboardmonitor.plist" 2>/dev/null || true
launchctl unload "$LAUNCH_AGENTS_DIR/com.clipboardmonitor.menubar.plist" 2>/dev/null || true

# Kill any running processes
pkill -f "ClipboardMonitor" 2>/dev/null || true
pkill -f "ClipboardMonitorMenuBar" 2>/dev/null || true

# Wait for processes to terminate
sleep 2

# Remove old plist files (they'll be replaced with new ones)
rm -f "$LAUNCH_AGENTS_DIR/com.clipboardmonitor.plist" 2>/dev/null || true
rm -f "$LAUNCH_AGENTS_DIR/com.clipboardmonitor.menubar.plist" 2>/dev/null || true

# Clean up old log files
rm -f "$LOG_DIR/ClipboardMonitor.out.log" 2>/dev/null || true
rm -f "$LOG_DIR/ClipboardMonitor.err.log" 2>/dev/null || true
rm -f "$LOG_DIR/ClipboardMonitorMenuBar.out.log" 2>/dev/null || true
rm -f "$LOG_DIR/ClipboardMonitorMenuBar.err.log" 2>/dev/null || true

echo "Previous installation cleaned up successfully"
exit 0
EOF
    chmod +x "pkg_scripts/preinstall"
}

# Create post-install script
create_postinstall_script() {
    print_status "Creating post-install script..."
    
    cat > "pkg_scripts/postinstall" << 'EOF'
#!/bin/bash
# Install and start services after app installation

USER_HOME=$(eval echo ~$USER)
LAUNCH_AGENTS_DIR="$USER_HOME/Library/LaunchAgents"
APP_RESOURCES="/Applications/Clipboard Monitor.app/Contents/Resources"

# Ensure LaunchAgents directory exists
mkdir -p "$LAUNCH_AGENTS_DIR"

# Copy plist files
cp "$APP_RESOURCES/com.clipboardmonitor.plist" "$LAUNCH_AGENTS_DIR/"
cp "$APP_RESOURCES/com.clipboardmonitor.menubar.plist" "$LAUNCH_AGENTS_DIR/"

# Load and start services
launchctl load "$LAUNCH_AGENTS_DIR/com.clipboardmonitor.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.clipboardmonitor.menubar.plist"

echo "Clipboard Monitor installed and started successfully!"
exit 0
EOF
    chmod +x "pkg_scripts/postinstall"
}

# Build PKG
build_pkg() {
    print_status "Building PKG installer..."
    
    if [[ "$QUIET_MODE" == "true" ]]; then
        pkgbuild \
            --root "pkg_root" \
            --scripts "pkg_scripts" \
            --identifier "$IDENTIFIER" \
            --version "$VERSION" \
            --install-location "/" \
            "$PKG_NAME" > /dev/null 2>&1
    else
        pkgbuild \
            --root "pkg_root" \
            --scripts "pkg_scripts" \
            --identifier "$IDENTIFIER" \
            --version "$VERSION" \
            --install-location "/" \
            "$PKG_NAME"
    fi
    
    print_success "PKG created: $PKG_NAME"
}

# Cleanup temporary files
cleanup() {
    print_status "Cleaning up temporary files..."
    rm -rf "pkg_root" "pkg_scripts" "pkg_resources"
}

# Main execution
main() {
    quiet_print_status "Starting PKG creation process..."

    create_package_structure
    create_preinstall_script
    create_postinstall_script
    build_pkg
    cleanup

    print_success "PKG installer ready for distribution!"
    if [[ "$QUIET_MODE" != "true" ]]; then
        echo "📦 File: $PKG_NAME"
        echo "📏 Size: $(du -sh "$PKG_NAME" | cut -f1)"
    fi
}

main "$@"
