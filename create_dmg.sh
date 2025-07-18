#!/bin/bash
set -e  # Exit on any error

# Clipboard Monitor DMG Creation Script
# Creates a professional DMG for distribution

# --- Configuration & Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_NAME="Clipboard Monitor"
APP_BUNDLE="Clipboard Monitor.app"
DMG_NAME="ClipboardMonitor-1.0"
DMG_TEMP_NAME="temp_${DMG_NAME}"
VOLUME_NAME="Clipboard Monitor"
DMG_SIZE="100m"  # Adjust size as needed

# Function to print colored output
print_status() {
    echo -e "${BLUE}📦 $1${NC}"
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to clean up previous DMG files
cleanup_dmg() {
    print_status "Cleaning up previous DMG files..."
    
    # Remove existing DMG files
    rm -f "${DMG_NAME}.dmg"
    rm -f "${DMG_TEMP_NAME}.dmg"
    
    # Unmount any existing volumes
    if [ -d "/Volumes/${VOLUME_NAME}" ]; then
        hdiutil detach "/Volumes/${VOLUME_NAME}" 2>/dev/null || true
    fi
    
    print_success "Cleanup completed"
}

# Function to create DMG
create_dmg() {
    print_status "Creating DMG..."
    
    # Check if app bundle exists
    if [ ! -d "$APP_BUNDLE" ]; then
        print_error "App bundle '$APP_BUNDLE' not found. Please run build_pyinstaller.sh first."
        exit 1
    fi
    
    # Create temporary DMG
    print_status "Creating temporary DMG..."
    hdiutil create -size "$DMG_SIZE" -fs HFS+ -volname "$VOLUME_NAME" "$DMG_TEMP_NAME.dmg"
    
    # Mount the temporary DMG
    print_status "Mounting temporary DMG..."
    hdiutil attach "$DMG_TEMP_NAME.dmg"
    
    # Copy app bundle to DMG
    print_status "Copying application to DMG..."
    ditto "$APP_BUNDLE" "/Volumes/${VOLUME_NAME}/$APP_BUNDLE"
    
    # Create Applications symlink for easy installation
    print_status "Creating Applications symlink..."
    ln -s /Applications "/Volumes/${VOLUME_NAME}/Applications"

    # Create LaunchAgents symlink for easy plist installation
    print_status "Creating LaunchAgents symlink..."
    ln -s "$HOME/Library/LaunchAgents" "/Volumes/${VOLUME_NAME}/LaunchAgents"
    
    # Copy additional files
    copy_additional_files
    
    # Set up DMG layout and appearance
    setup_dmg_appearance
    
    # Unmount the temporary DMG
    print_status "Unmounting temporary DMG..."
    hdiutil detach "/Volumes/${VOLUME_NAME}"
    
    # Convert to compressed, read-only DMG
    print_status "Creating final compressed DMG..."
    hdiutil convert "$DMG_TEMP_NAME.dmg" -format UDZO -o "$DMG_NAME.dmg"
    
    # Clean up temporary DMG
    rm -f "$DMG_TEMP_NAME.dmg"
    
    print_success "DMG created: $DMG_NAME.dmg"
}

# Function to copy additional files to DMG
copy_additional_files() {
    print_status "Adding additional files to DMG..."
    
    # Copy README file
    if [ -f "README.txt" ]; then
        cp "README.txt" "/Volumes/${VOLUME_NAME}/"
    else
        create_readme_file "/Volumes/${VOLUME_NAME}/README.txt"
    fi
    
    # Copy install script if it exists
    if [ -f "install.sh" ]; then
        cp "install.sh" "/Volumes/${VOLUME_NAME}/"
        chmod +x "/Volumes/${VOLUME_NAME}/install.sh"
    fi
    
    # Copy uninstall script if it exists
    if [ -f "uninstall.sh" ]; then
        cp "uninstall.sh" "/Volumes/${VOLUME_NAME}/"
        chmod +x "/Volumes/${VOLUME_NAME}/uninstall.sh"
    fi

    # Copy plist files for manual installation
    if [ -f "plist_files/com.clipboardmonitor.plist" ]; then
        cp "plist_files/com.clipboardmonitor.plist" "/Volumes/${VOLUME_NAME}/"
    fi

    if [ -f "plist_files/com.clipboardmonitor.menubar.plist" ]; then
        cp "plist_files/com.clipboardmonitor.menubar.plist" "/Volumes/${VOLUME_NAME}/"
    fi

    print_success "Additional files added"
}

# Function to create README file
create_readme_file() {
    local readme_path="$1"
    
    cat > "$readme_path" << EOF
Clipboard Monitor v1.0
======================

Thank you for downloading Clipboard Monitor!

INSTALLATION:
1. Drag "Clipboard Monitor.app" to the Applications folder
2. Run the install.sh script to set up background services
3. MANUAL STEP: Copy the plist files to ~/Library/LaunchAgents/ when prompted
   - com.clipboardmonitor.plist
   - com.clipboardmonitor.menubar.plist
   - TIP: Use the LaunchAgents symlink for easy drag-and-drop installation
4. The app will appear in your menu bar

NOTE: Manual plist installation is required due to SentinelOne security software.
The LaunchAgents symlink provides direct access to your LaunchAgents folder.

FEATURES:
- Real-time clipboard monitoring
- Modular content processing
- History tracking
- Menu bar interface
- Memory monitoring and optimization

SYSTEM REQUIREMENTS:
- macOS 10.14 or later
- No additional dependencies required (fully self-contained)

SUPPORT:
For support and documentation, visit:
https://github.com/omairaslam/Clipboard-Monitor

UNINSTALLATION:
To remove the application:
1. Run the uninstall.sh script
2. Drag the app to Trash

Copyright © 2025 Clipboard Monitor
EOF
}

# Function to set up DMG appearance and layout
setup_dmg_appearance() {
    print_status "Setting up DMG appearance..."

    # Use AppleScript to set up the DMG window appearance with list view
    osascript << EOF
tell application "Finder"
    tell disk "$VOLUME_NAME"
        open
        set current view of container window to list view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {400, 100, 900, 500}

        -- Configure basic list view options
        set viewOptions to the list view options of container window
        set text size of viewOptions to 12
        set icon size of viewOptions to small icon
        set calculates folder sizes of viewOptions to false

        close
        open
        update without registering applications
        delay 3
    end tell
end tell
EOF

    print_success "DMG appearance configured"
}

# Function to sign the DMG (optional)
sign_dmg() {
    if command_exists codesign; then
        print_status "Checking for code signing certificate..."
        
        # Check if we have a valid signing identity
        if security find-identity -v -p codesigning | grep -q "Developer ID Application"; then
            print_status "Signing DMG..."
            codesign --sign "Developer ID Application" "$DMG_NAME.dmg"
            print_success "DMG signed successfully"
        else
            print_warning "No code signing certificate found. DMG will not be signed."
        fi
    else
        print_warning "codesign not available. DMG will not be signed."
    fi
}

# Function to verify DMG
verify_dmg() {
    print_status "Verifying DMG..."
    
    # Check if DMG can be mounted
    if hdiutil attach "$DMG_NAME.dmg" -readonly -nobrowse; then
        # Check if app bundle exists in mounted volume
        if [ -d "/Volumes/${VOLUME_NAME}/$APP_BUNDLE" ]; then
            print_success "DMG verification passed"
        else
            print_error "App bundle not found in DMG"
            exit 1
        fi
        
        # Unmount verification volume
        hdiutil detach "/Volumes/${VOLUME_NAME}"
    else
        print_error "Failed to mount DMG for verification"
        exit 1
    fi
}

# Main DMG creation process
main() {
    echo "🚀 Starting Clipboard Monitor DMG Creation"
    echo "==========================================="
    
    # Check if we're in the right directory
    if [ ! -f "build_pyinstaller.sh" ]; then
        print_error "Please run this script from the Clipboard Monitor project root directory"
        exit 1
    fi
    
    cleanup_dmg
    create_dmg
    sign_dmg
    verify_dmg
    
    echo ""
    echo "==========================================="
    print_success "DMG creation completed successfully!"
    echo ""
    echo "📱 DMG file: $DMG_NAME.dmg"
    echo "📁 Size: $(du -sh "$DMG_NAME.dmg" | cut -f1)"
    echo ""
    echo "🔧 Next steps:"
    echo "  1. Test the DMG: open '$DMG_NAME.dmg'"
    echo "  2. Distribute the DMG file"
    echo "  3. Users can drag the app to Applications and run install.sh"
    echo ""
}

# Run main function
main "$@"
