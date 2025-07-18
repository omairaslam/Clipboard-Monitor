#!/bin/bash
set -e  # Exit on any error

# Unified Build, Create, and Test DMG Script
# Combines build_pyinstaller.sh, create_dmg.sh, and test_dmg_workflow.sh
# into a single automated workflow

# --- Configuration & Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# App Configuration
APP_NAME="Clipboard Monitor"
BUNDLE_ID="com.clipboardmonitor.app"
VERSION="1.0.0"
BUILD_DIR="build_pyinstaller"
DIST_DIR="dist_pyinstaller"
FINAL_APP_NAME="Clipboard Monitor.app"

# DMG Configuration
DMG_NAME="ClipboardMonitor-1.0"
DMG_TEMP_NAME="temp_${DMG_NAME}"
VOLUME_NAME="Clipboard Monitor"
DMG_SIZE="100m"

# Test Configuration
TEST_DIR="/tmp/clipboard_monitor_test"

# Function to print colored output
print_header() {
    echo -e "${PURPLE}================================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}================================================${NC}"
}

print_section() {
    echo -e "${CYAN}🔧 $1${NC}"
}

print_status() {
    if [[ "$QUIET_MODE" == "true" ]]; then
        echo -e "${BLUE}📦 $1${NC}"
    else
        echo -e "${BLUE}📦 $1${NC}"
    fi
}

print_success() {
    if [[ "$QUIET_MODE" == "true" ]]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${GREEN}✅ $1${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Quiet versions that only show in verbose mode
quiet_status() {
    if [[ "$QUIET_MODE" != "true" ]]; then
        echo -e "${BLUE}📦 $1${NC}"
    fi
}

quiet_success() {
    if [[ "$QUIET_MODE" != "true" ]]; then
        echo -e "${GREEN}✅ $1${NC}"
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================================================
# BUILD PHASE - From build_pyinstaller.sh
# ============================================================================

# Function to clean previous builds
clean_build() {
    print_status "Cleaning previous builds..."
    
    # Remove PyInstaller build directories
    rm -rf "$BUILD_DIR"
    rm -rf "$DIST_DIR"
    rm -rf "build"
    rm -rf "dist"
    
    # Remove spec file generated directories
    rm -rf "ClipboardMonitor"
    rm -rf "ClipboardMonitorMenuBar"
    
    # Remove any existing final app
    rm -rf "$FINAL_APP_NAME"
    
    # Remove existing DMG files
    rm -f "${DMG_NAME}.dmg"
    rm -f "${DMG_TEMP_NAME}.dmg"
    
    # Unmount any existing volumes (including numbered variants)
    for vol in "/Volumes/${VOLUME_NAME}" "/Volumes/${VOLUME_NAME} 1" "/Volumes/${VOLUME_NAME} 2"; do
        if [ -d "$vol" ]; then
            print_status "Unmounting existing volume: $vol"
            hdiutil detach "$vol" 2>/dev/null || diskutil unmount force "$vol" 2>/dev/null || true
        fi
    done
    
    print_success "Build directories and previous DMG files cleaned"
}

# Function to activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."

    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        print_error "Virtual environment not found. Please create it first with: python3 -m venv .venv"
        exit 1
    fi

    # Activate virtual environment
    source .venv/bin/activate

    # Verify activation
    if [ "$VIRTUAL_ENV" = "" ]; then
        print_error "Failed to activate virtual environment"
        exit 1
    fi

    print_success "Virtual environment activated: $VIRTUAL_ENV"
}

# Function to check and install dependencies
check_dependencies() {
    print_status "Checking dependencies..."

    # Check if Python is available (should be from venv)
    if ! command_exists python; then
        print_error "Python is required but not available in virtual environment"
        exit 1
    fi

    # Check if pip is available (should be from venv)
    if ! command_exists pip; then
        print_error "pip is required but not available in virtual environment"
        exit 1
    fi

    # Install project dependencies
    print_status "Installing project dependencies..."
    if [[ "$QUIET_MODE" == "true" ]]; then
        pip install -r requirements.txt > /dev/null 2>&1
    else
        pip install -r requirements.txt
    fi

    print_success "Dependencies checked and installed"
}

# Function to build executables
build_executables() {
    print_status "Building executables with PyInstaller..."
    
    # Create build and dist directories
    mkdir -p "$BUILD_DIR"
    mkdir -p "$DIST_DIR"
    
    # Build main service executable
    print_status "Building main service executable..."
    if [[ "$QUIET_MODE" == "true" ]]; then
        python -m PyInstaller --distpath "$DIST_DIR" --workpath "$BUILD_DIR" main.spec --log-level WARN > /dev/null 2>&1
    else
        python -m PyInstaller --distpath "$DIST_DIR" --workpath "$BUILD_DIR" main.spec
    fi

    if [ ! -d "$DIST_DIR/ClipboardMonitor.app" ]; then
        print_error "Failed to build main service executable"
        exit 1
    fi

    # Build menu bar app executable
    print_status "Building menu bar app executable..."
    if [[ "$QUIET_MODE" == "true" ]]; then
        python -m PyInstaller --distpath "$DIST_DIR" --workpath "$BUILD_DIR" menu_bar_app.spec --log-level WARN > /dev/null 2>&1
    else
        python -m PyInstaller --distpath "$DIST_DIR" --workpath "$BUILD_DIR" menu_bar_app.spec
    fi

    if [ ! -d "$DIST_DIR/ClipboardMonitorMenuBar.app" ]; then
        print_error "Failed to build menu bar app executable"
        exit 1
    fi
    
    print_success "Executables built successfully"
}

# Function to create Info.plist
create_info_plist() {
    local plist_path="$1"
    
    cat > "$plist_path" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundleExecutable</key>
    <string>ClipboardMonitorMenuBar</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSUIElement</key>
    <true/>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2025 Clipboard Monitor</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.utilities</string>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
EOF
}

# Function to create unified app bundle
create_app_bundle() {
    print_status "Creating unified app bundle..."
    
    # Create the main app bundle structure
    APP_BUNDLE="$FINAL_APP_NAME"
    CONTENTS_DIR="$APP_BUNDLE/Contents"
    MACOS_DIR="$CONTENTS_DIR/MacOS"
    RESOURCES_DIR="$CONTENTS_DIR/Resources"
    
    # Create directory structure
    mkdir -p "$MACOS_DIR"
    mkdir -p "$RESOURCES_DIR"
    
    # Copy the menu bar app as the main executable (it's the user-facing component)
    cp -R "$DIST_DIR/ClipboardMonitorMenuBar.app/Contents/MacOS/"* "$MACOS_DIR/"
    cp -R "$DIST_DIR/ClipboardMonitorMenuBar.app/Contents/Resources/"* "$RESOURCES_DIR/"

    # Copy Frameworks directory (essential for PyInstaller apps)
    if [ -d "$DIST_DIR/ClipboardMonitorMenuBar.app/Contents/Frameworks" ]; then
        cp -R "$DIST_DIR/ClipboardMonitorMenuBar.app/Contents/Frameworks" "$CONTENTS_DIR/"
    fi

    # Copy the entire background service app bundle into Resources
    # PyInstaller apps need their complete bundle structure to run properly
    mkdir -p "$RESOURCES_DIR/Services"
    cp -R "$DIST_DIR/ClipboardMonitor.app" "$RESOURCES_DIR/Services/"

    # Also merge any additional resources from the background service
    if [ -d "$DIST_DIR/ClipboardMonitor.app/Contents/Resources" ]; then
        # Copy any files that aren't already in the main Resources directory
        if [[ "$QUIET_MODE" == "true" ]]; then
            rsync -a --ignore-existing "$DIST_DIR/ClipboardMonitor.app/Contents/Resources/" "$RESOURCES_DIR/" > /dev/null 2>&1
        else
            rsync -av --ignore-existing "$DIST_DIR/ClipboardMonitor.app/Contents/Resources/" "$RESOURCES_DIR/"
        fi
    fi
    
    # Create the main Info.plist
    create_info_plist "$CONTENTS_DIR/Info.plist"
    
    print_success "App bundle created: $APP_BUNDLE"
}

# Function to update plist templates for bundled executables
update_plist_templates() {
    print_status "Updating plist templates for bundled executables..."
    
    # Create updated plist templates in Resources
    local resources_dir="$FINAL_APP_NAME/Contents/Resources"
    
    # Update main service plist template
    sed "s|/usr/bin/python3|$PWD/$FINAL_APP_NAME/Contents/Resources/Services/ClipboardMonitor.app/Contents/MacOS/ClipboardMonitor|g" \
        plist_files/com.clipboardmonitor.plist > "$resources_dir/com.clipboardmonitor.plist"

    # Update menu bar plist template
    sed "s|/usr/bin/python3|$PWD/$FINAL_APP_NAME/Contents/MacOS/ClipboardMonitorMenuBar|g" \
        plist_files/com.clipboardmonitor.menubar.plist > "$resources_dir/com.clipboardmonitor.menubar.plist"
    
    print_success "Plist templates updated"
}

# ============================================================================
# DMG CREATION PHASE - From create_dmg.sh
# ============================================================================

# Function to create DMG
create_dmg() {
    print_status "Creating DMG..."

    # Check if app bundle exists
    if [ ! -d "$FINAL_APP_NAME" ]; then
        print_error "App bundle '$FINAL_APP_NAME' not found"
        exit 1
    fi

    # Create temporary DMG
    print_status "Creating temporary DMG..."
    if [[ "$QUIET_MODE" == "true" ]]; then
        hdiutil create -size "$DMG_SIZE" -fs HFS+ -volname "$VOLUME_NAME" "${DMG_TEMP_NAME}.dmg" > /dev/null 2>&1
    else
        hdiutil create -size "$DMG_SIZE" -fs HFS+ -volname "$VOLUME_NAME" "${DMG_TEMP_NAME}.dmg"
    fi

    # Mount temporary DMG
    print_status "Mounting temporary DMG..."
    if [[ "$QUIET_MODE" == "true" ]]; then
        hdiutil attach "${DMG_TEMP_NAME}.dmg" -readwrite -nobrowse -noautoopen > /dev/null 2>&1
    else
        hdiutil attach "${DMG_TEMP_NAME}.dmg" -readwrite -nobrowse -noautoopen
    fi

    # Wait for mount to be ready
    sleep 2

    # Verify mount is read-write
    if [ ! -w "/Volumes/${VOLUME_NAME}" ]; then
        print_error "DMG volume is not writable"
        hdiutil detach "/Volumes/${VOLUME_NAME}" 2>/dev/null || true
        exit 1
    fi

    # Copy app to DMG
    print_status "Copying app to DMG..."
    if ! ditto "$FINAL_APP_NAME" "/Volumes/${VOLUME_NAME}/$FINAL_APP_NAME"; then
        print_error "Failed to copy app to DMG"
        hdiutil detach "/Volumes/${VOLUME_NAME}" 2>/dev/null || true
        exit 1
    fi

    # Copy plist files to DMG root for easy access
    print_status "Copying plist files to DMG..."
    if ! cp "$FINAL_APP_NAME/Contents/Resources/com.clipboardmonitor.plist" "/Volumes/${VOLUME_NAME}/"; then
        print_error "Failed to copy main service plist"
        hdiutil detach "/Volumes/${VOLUME_NAME}" 2>/dev/null || true
        exit 1
    fi
    if ! cp "$FINAL_APP_NAME/Contents/Resources/com.clipboardmonitor.menubar.plist" "/Volumes/${VOLUME_NAME}/"; then
        print_error "Failed to copy menu bar service plist"
        hdiutil detach "/Volumes/${VOLUME_NAME}" 2>/dev/null || true
        exit 1
    fi

    # Create Applications symlink
    print_status "Creating Applications symlink..."
    if ! ln -s /Applications "/Volumes/${VOLUME_NAME}/Applications"; then
        print_error "Failed to create Applications symlink"
        hdiutil detach "/Volumes/${VOLUME_NAME}" 2>/dev/null || true
        exit 1
    fi

    # Create LaunchAgents symlink for easy plist installation
    print_status "Creating LaunchAgents symlink..."
    if ! ln -s "$HOME/Library/LaunchAgents" "/Volumes/${VOLUME_NAME}/LaunchAgents"; then
        print_error "Failed to create LaunchAgents symlink"
        hdiutil detach "/Volumes/${VOLUME_NAME}" 2>/dev/null || true
        exit 1
    fi

    # Copy install script
    print_status "Copying install script..."
    if ! cp install.sh "/Volumes/${VOLUME_NAME}/"; then
        print_error "Failed to copy install script"
        hdiutil detach "/Volumes/${VOLUME_NAME}" 2>/dev/null || true
        exit 1
    fi
    chmod +x "/Volumes/${VOLUME_NAME}/install.sh"

    # Copy uninstall script
    print_status "Copying uninstall script..."
    if ! cp uninstall.sh "/Volumes/${VOLUME_NAME}/"; then
        print_error "Failed to copy uninstall script"
        hdiutil detach "/Volumes/${VOLUME_NAME}" 2>/dev/null || true
        exit 1
    fi
    chmod +x "/Volumes/${VOLUME_NAME}/uninstall.sh"

    # Create README
    create_readme "/Volumes/${VOLUME_NAME}/README.txt"

    # Set DMG background and layout (if available)
    setup_dmg_appearance "/Volumes/${VOLUME_NAME}"

    # Unmount DMG
    print_status "Unmounting DMG..."
    if [[ "$QUIET_MODE" == "true" ]]; then
        hdiutil detach "/Volumes/${VOLUME_NAME}" > /dev/null 2>&1
    else
        hdiutil detach "/Volumes/${VOLUME_NAME}"
    fi

    # Convert to final compressed DMG
    print_status "Converting to final compressed DMG..."
    if [[ "$QUIET_MODE" == "true" ]]; then
        hdiutil convert "${DMG_TEMP_NAME}.dmg" -format UDZO -o "${DMG_NAME}.dmg" > /dev/null 2>&1
    else
        hdiutil convert "${DMG_TEMP_NAME}.dmg" -format UDZO -o "${DMG_NAME}.dmg"
    fi

    # Remove temporary DMG
    rm "${DMG_TEMP_NAME}.dmg"

    print_success "DMG created: ${DMG_NAME}.dmg"
}

# Function to create README file
create_readme() {
    local readme_path="$1"

    cat > "$readme_path" << EOF
Clipboard Monitor v${VERSION}
============================

Thank you for downloading Clipboard Monitor!

🚀 EASY INSTALLATION:
1. Drag "Clipboard Monitor.app" to the Applications folder
2. Double-click the install.sh script to set up background services
3. The script will open both the DMG and LaunchAgents folders for you
4. Simply drag the 2 plist files to the LaunchAgents folder
5. Return to the script and press any key to complete installation
6. The app will start automatically and appear in your menu bar

📁 WHAT'S INCLUDED:
- Clipboard Monitor.app (main application)
- com.clipboardmonitor.plist (background service configuration)
- com.clipboardmonitor.menubar.plist (menu bar service configuration)
- LaunchAgents folder (shortcut to ~/Library/LaunchAgents)
- install.sh (automated installation script)
- uninstall.sh (complete removal script)

✨ FEATURES:
- Clipboard history tracking with intelligent categorization
- Menu bar access to recent items with search
- Support for text, images, rich content, and code
- Automatic startup with macOS
- Memory-optimized background service
- Advanced memory monitoring and leak detection
- Modular architecture with plugin support

🗑️ UNINSTALLATION:
- Run the uninstall.sh script to completely remove the app and services
- Or run: ./install.sh --uninstall

📋 REQUIREMENTS:
- macOS 10.14 or later
- No additional software required (self-contained)

🆘 SUPPORT:
For issues or questions, check the built-in memory dashboard at localhost:8001
when advanced monitoring is enabled through the menu bar.

Copyright © 2025 Clipboard Monitor
EOF
}

# Function to setup DMG appearance
setup_dmg_appearance() {
    print_status "Setting up DMG appearance..."

    # Use AppleScript to set up the DMG window appearance
    osascript << EOF
tell application "Finder"
    tell disk "$VOLUME_NAME"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {400, 100, 900, 400}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 72

        -- Position items
        set position of item "$FINAL_APP_NAME" of container window to {150, 150}
        set position of item "Applications" of container window to {350, 150}

        close
        open
        update without registering applications
        delay 2
    end tell
end tell
EOF

    print_success "DMG appearance configured"
}

# ============================================================================
# TESTING PHASE - From test_dmg_workflow.sh
# ============================================================================

# Function to cleanup test environment
cleanup_test() {
    print_status "Cleaning up test environment..."

    # Remove test directory
    rm -rf "$TEST_DIR"

    # Unmount any test volumes
    if [ -d "/Volumes/${VOLUME_NAME}" ]; then
        hdiutil detach "/Volumes/${VOLUME_NAME}" 2>/dev/null || true
    fi

    print_success "Test environment cleaned"
}

# Function to test DMG mounting and contents
test_dmg_mounting() {
    print_status "Testing DMG mounting and contents..."

    # Check if DMG exists
    if [ ! -f "${DMG_NAME}.dmg" ]; then
        print_error "DMG file '${DMG_NAME}.dmg' not found"
        return 1
    fi

    # Mount DMG
    print_status "Mounting DMG for testing..."
    if [[ "$QUIET_MODE" == "true" ]]; then
        hdiutil attach "${DMG_NAME}.dmg" -readonly -nobrowse > /dev/null 2>&1
    else
        hdiutil attach "${DMG_NAME}.dmg" -readonly -nobrowse
    fi

    # Check DMG contents
    print_status "Verifying DMG contents..."

    # Check if app bundle exists
    if [ ! -d "/Volumes/${VOLUME_NAME}/$FINAL_APP_NAME" ]; then
        print_error "App bundle not found in DMG"
        return 1
    fi

    # Check if Applications symlink exists
    if [ ! -L "/Volumes/${VOLUME_NAME}/Applications" ]; then
        print_error "Applications symlink not found in DMG"
        return 1
    fi

    # Check if install script exists
    if [ ! -f "/Volumes/${VOLUME_NAME}/install.sh" ]; then
        print_error "install.sh not found in DMG"
        return 1
    fi

    # Check if README exists
    if [ ! -f "/Volumes/${VOLUME_NAME}/README.txt" ]; then
        print_error "README.txt not found in DMG"
        return 1
    fi

    # Check if plist files exist
    if [ ! -f "/Volumes/${VOLUME_NAME}/com.clipboardmonitor.plist" ]; then
        print_error "com.clipboardmonitor.plist not found in DMG"
        return 1
    fi

    if [ ! -f "/Volumes/${VOLUME_NAME}/com.clipboardmonitor.menubar.plist" ]; then
        print_error "com.clipboardmonitor.menubar.plist not found in DMG"
        return 1
    fi

    # Check if LaunchAgents symlink exists
    if [ ! -L "/Volumes/${VOLUME_NAME}/LaunchAgents" ]; then
        print_error "LaunchAgents symlink not found in DMG"
        return 1
    fi

    print_success "DMG contents verified"
    return 0
}

# Function to test app bundle structure
test_app_bundle() {
    print_status "Testing app bundle structure..."

    local app_path="/Volumes/${VOLUME_NAME}/$FINAL_APP_NAME"

    # Check main executable
    if [ ! -f "$app_path/Contents/MacOS/ClipboardMonitorMenuBar" ]; then
        print_error "Main executable not found"
        return 1
    fi

    # Check background service executable
    if [ ! -f "$app_path/Contents/Resources/Services/ClipboardMonitor.app/Contents/MacOS/ClipboardMonitor" ]; then
        print_error "Background service executable not found"
        return 1
    fi

    # Check Frameworks directory
    if [ ! -d "$app_path/Contents/Frameworks" ]; then
        print_error "Frameworks directory not found"
        return 1
    fi

    # Check Info.plist
    if [ ! -f "$app_path/Contents/Info.plist" ]; then
        print_error "Info.plist not found"
        return 1
    fi

    # Check essential files
    if [ ! -f "$app_path/Contents/Resources/config.json" ]; then
        print_error "config.json not found"
        return 1
    fi

    # Check modules directory
    if [ ! -d "$app_path/Contents/Resources/modules" ]; then
        print_error "modules directory not found"
        return 1
    fi

    print_success "App bundle structure verified"
    return 0
}

# Function to test file permissions
test_permissions() {
    print_status "Testing file permissions..."

    local app_path="/Volumes/${VOLUME_NAME}/$FINAL_APP_NAME"

    # Check if executables are executable
    if [ ! -x "$app_path/Contents/MacOS/ClipboardMonitorMenuBar" ]; then
        print_error "Main executable is not executable"
        return 1
    fi

    if [ ! -x "$app_path/Contents/Resources/Services/ClipboardMonitor.app/Contents/MacOS/ClipboardMonitor" ]; then
        print_error "Background service executable is not executable"
        return 1
    fi

    if [ ! -x "/Volumes/${VOLUME_NAME}/install.sh" ]; then
        print_error "install.sh is not executable"
        return 1
    fi

    print_success "File permissions verified"
    return 0
}

# Function to display DMG information
display_dmg_info() {
    print_status "DMG Information:"
    echo "  📁 File: ${DMG_NAME}.dmg"
    echo "  📏 Size: $(du -sh "${DMG_NAME}.dmg" | cut -f1)"
    echo "  🔍 Type: $(file "${DMG_NAME}.dmg")"
    echo ""

    print_status "App Bundle Information:"
    local app_path="/Volumes/${VOLUME_NAME}/$FINAL_APP_NAME"
    echo "  📱 Bundle: $FINAL_APP_NAME"
    echo "  📏 Size: $(du -sh "$app_path" | cut -f1)"
    echo "  🆔 Bundle ID: $(defaults read "$app_path/Contents/Info.plist" CFBundleIdentifier 2>/dev/null || echo "Unknown")"
    echo "  📋 Version: $(defaults read "$app_path/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo "Unknown")"
    echo ""
}

# ============================================================================
# PHASE 4: GUIDED INSTALLATION TEST
# ============================================================================

# Main function for the guided installation test phase
run_guided_installation_test() {
    print_section "Guided Installation Test"
    echo ""
    echo "The DMG has been created successfully! 🎉"
    echo ""

    # 1. Clean up any previous installation
    cleanup_existing_installation

    # 2. Simulate user copying .app to /Applications
    copy_app_to_applications_for_test

    # 3. Open folders for manual plist copy
    open_folders_for_manual_installation

    # 4. Wait for user to copy plists and confirm
    wait_for_plist_confirmation

    # 5. Verify that the app and plists are in the correct locations
    if verify_manual_installation; then
        # 6. Load the services to start the application
        load_services_for_test
    else
        print_error "Installation verification failed. Cannot start services."
        exit 1
    fi
}

# Function to cleanup existing installation before testing new DMG
cleanup_existing_installation() {
    print_status "Running complete uninstall to clean up any existing installation..."
    if [ ! -f "./uninstall.sh" ]; then
        print_error "uninstall.sh not found - using basic cleanup"
        basic_cleanup_fallback
        return
    fi
    chmod +x ./uninstall.sh
    echo ""
    echo -e "${BLUE}🧹 Running automated uninstall to ensure clean state...${NC}"
    echo ""
    if [[ "$QUIET_MODE" == "true" ]]; then
        echo "y" | ./uninstall.sh 2>/dev/null | grep -E "(✅|❌|⚠️|🎉)" || true
    else
        echo "y" | ./uninstall.sh
    fi
    echo ""
    print_success "Uninstall completed - system is clean for fresh installation"
    echo ""
}

basic_cleanup_fallback() {
    print_status "Performing basic cleanup..."
    local launch_agents_dir="$HOME/Library/LaunchAgents"
    local main_plist="$launch_agents_dir/com.clipboardmonitor.plist"
    local menubar_plist="$launch_agents_dir/com.clipboardmonitor.menubar.plist"
    launchctl unload "$main_plist" 2>/dev/null || true
    launchctl unload "$menubar_plist" 2>/dev/null || true
    rm -f "$main_plist" "$menubar_plist"
    pkill -f "ClipboardMonitor" 2>/dev/null || true
    print_success "Basic cleanup completed"
}

# Function to copy the .app to /Applications for testing
copy_app_to_applications_for_test() {
    print_status "Simulating user action: Copying app to /Applications..."
    local app_in_dmg="/Volumes/${VOLUME_NAME}/$FINAL_APP_NAME"
    local app_in_apps="/Applications/$FINAL_APP_NAME"

    if [ ! -d "$app_in_dmg" ]; then
        print_error "Cannot copy app. DMG not mounted or app not found in DMG."
        return 1
    fi

    if [ -d "$app_in_apps" ]; then
        print_warning "Removing existing app from /Applications to simulate clean install."
        rm -rf "$app_in_apps"
    fi

    if ditto "$app_in_dmg" "$app_in_apps"; then
        print_success "App successfully copied to /Applications"
    else
        print_error "Failed to copy app to /Applications"
        return 1
    fi
}

# Function to open folders for manual installation
open_folders_for_manual_installation() {
    print_status "Opening folders for manual installation..."
    mkdir -p "$HOME/Library/LaunchAgents"
    if [ ! -d "/Volumes/${VOLUME_NAME}" ]; then
        print_status "Mounting DMG for manual installation..."
        if [[ "$QUIET_MODE" == "true" ]]; then
            hdiutil attach "${DMG_NAME}.dmg" -readonly -nobrowse > /dev/null 2>&1
        else
            hdiutil attach "${DMG_NAME}.dmg" -readonly -nobrowse
        fi
    fi
    if [ ! -d "/Volumes/${VOLUME_NAME}" ]; then
        print_error "Failed to mount DMG. Please mount ${DMG_NAME}.dmg manually."
        return 1
    fi

    open "/Volumes/${VOLUME_NAME}"
    print_success "Opened DMG folder"
    open "$HOME/Library/LaunchAgents"
    print_success "Opened LaunchAgents folder"

    echo ""
    echo -e "${GREEN}✨ Both folders are now open!${NC}"
    echo -e "${BLUE}📋 Please drag these 2 files from the DMG folder to the LaunchAgents folder:${NC}"
    echo "     • com.clipboardmonitor.plist"
    echo "     • com.clipboardmonitor.menubar.plist"
    echo ""
}

# Function to wait for user confirmation that plist files have been copied
wait_for_plist_confirmation() {
    echo -e "${BLUE}⏳ Waiting for you to copy the plist files...${NC}"
    echo ""
    echo -e "${GREEN}💡 Tip: Just press Enter to proceed (defaults to Yes)${NC}"
    echo ""

    while true; do
        read -p "Have you copied both plist files to the LaunchAgents folder? (Y/n): " yn
        if [[ -z "$yn" ]]; then
            yn="y"
            echo "y"  # Show the default choice
        fi

        case $yn in
            [Yy]* )
                print_success "Great! Proceeding with verification..."
                break
                ;;
            [Nn]* )
                echo ""
                echo -e "${YELLOW}⏳ Take your time! The folders are still open.${NC}"
                echo ""
                ;;
            * )
                echo "Please answer yes (y) or no (n), or just press Enter for yes."
                ;;
        esac
    done
}

# Function to verify manual installation of app and plists
verify_manual_installation() {
    echo ""
    print_status "Verifying manual installation steps..."

    local launch_agents_dir="$HOME/Library/LaunchAgents"
    local main_plist="$launch_agents_dir/com.clipboardmonitor.plist"
    local menubar_plist="$launch_agents_dir/com.clipboardmonitor.menubar.plist"
    local app_in_apps="/Applications/$FINAL_APP_NAME"
    local verification_passed=true

    if [ -d "$app_in_apps" ]; then
        print_success "Found app in /Applications"
    else
        print_error "App not found in /Applications"
        verification_passed=false
    fi

    if [ -f "$main_plist" ]; then
        print_success "Found main service plist: com.clipboardmonitor.plist"
    else
        print_error "Missing main service plist: com.clipboardmonitor.plist"
        verification_passed=false
    fi

    if [ -f "$menubar_plist" ]; then
        print_success "Found menubar service plist: com.clipboardmonitor.menubar.plist"
    else
        print_error "Missing menubar service plist: com.clipboardmonitor.menubar.plist"
        verification_passed=false
    fi

    if [ "$verification_passed" = true ]; then
        echo ""
        print_success "✅ All installation components are in place!"
        return 0
    else
        echo ""
        print_error "Verification failed. Please check the missing components."
        return 1
    fi
}

# Function to load services via launchctl
load_services_for_test() {
    print_status "Loading services via launchctl..."
    local launch_agents_dir="$HOME/Library/LaunchAgents"
    local main_plist="$launch_agents_dir/com.clipboardmonitor.plist"
    local menubar_plist="$launch_agents_dir/com.clipboardmonitor.menubar.plist"

    # Unload first to ensure a clean start
    launchctl unload "$main_plist" 2>/dev/null || true
    launchctl unload "$menubar_plist" 2>/dev/null || true
    sleep 1

    # Load services
    if launchctl load "$main_plist"; then
        print_success "Background service loaded"
    else
        print_error "Failed to load background service"
        return 1
    fi

    if launchctl load "$menubar_plist"; then
        print_success "Menu bar service loaded"
    else
        print_error "Failed to load menu bar service"
        launchctl unload "$main_plist" 2>/dev/null || true
        return 1
    fi

    echo ""
    print_status "Waiting for services to initialize..."
    sleep 3

    local bg_running=$(launchctl list | grep com.clipboardmonitor | grep -v menubar | wc -l)
    local mb_running=$(launchctl list | grep com.clipboardmonitor.menubar | wc -l)

    if [[ "$bg_running" -gt 0 && "$mb_running" -gt 0 ]]; then
        print_success "Services are running! Check your menu bar for the icon."
    else
        print_warning "Services loaded but may not be running correctly. Check logs."
        launchctl list | grep com.clipboardmonitor
    fi
}

# ============================================================================
# MAIN EXECUTION FUNCTION
# ============================================================================

# Main function
main() {
    if [[ "$QUIET_MODE" == "true" ]]; then
        print_header "🚀 Clipboard Monitor - Quiet Build"
        echo ""
        echo -e "${BLUE}Running in quiet mode - showing only essential progress...${NC}"
        echo ""
    else
        print_header "🚀 Unified Build, Create, and Test DMG Workflow"
        echo ""
        echo "This script will:"
        echo "  1. 🔨 Build PyInstaller executables"
        echo "  2. 📦 Create unified app bundle"
        echo "  3. 💿 Generate DMG file"
        echo "  4. 🧪 Test DMG integrity"
        echo "  5. 🎯 Provide manual installation guidance"
        echo ""
    fi

    # Phase 1: Build
    print_header "Phase 1: Building Executables"
    clean_build
    activate_venv
    check_dependencies
    build_executables
    create_app_bundle
    update_plist_templates
    print_success "Build phase completed successfully!"
    echo ""

    # Phase 2: Create DMG
    print_header "Phase 2: Creating DMG"
    create_dmg
    print_success "DMG creation phase completed successfully!"
    echo ""

    # Phase 3: Test DMG
    print_header "Phase 3: Testing DMG"
    local test_results=0

    cleanup_test

    if test_dmg_mounting; then
        print_success "DMG mounting test passed"
    else
        print_error "DMG mounting test failed"
        test_results=1
    fi

    if test_app_bundle; then
        print_success "App bundle test passed"
    else
        print_error "App bundle test failed"
        test_results=1
    fi

    if test_permissions; then
        print_success "Permissions test passed"
    else
        print_error "Permissions test failed"
        test_results=1
    fi

    # Display information
    echo ""
    display_dmg_info

    # Final results
    print_header "🎉 Workflow Complete!"
    if [ $test_results -eq 0 ]; then
        print_success "All tests passed! DMG is ready for distribution."
        echo ""
        echo "📁 Generated files:"
        echo "  • ${DMG_NAME}.dmg (Ready for distribution)"
        echo "  • $FINAL_APP_NAME (App bundle)"
        echo ""

        # Phase 4: Guided installation test
        run_guided_installation_test

    else
        print_error "Some tests failed. Please review the issues above."
        cleanup_test
        exit 1
    fi

    # Final cleanup
    cleanup_test

    print_header "✨ Success! Your DMG is ready for distribution!"
    echo ""
    echo "🚀 Next steps:"
    echo "  1. Test the DMG on a clean machine"
    echo "  2. Distribute ${DMG_NAME}.dmg to users"
    echo "  3. Users can drag to Applications and run install.sh"
    echo ""
}

# Function to parse command line arguments
parse_arguments() {
    QUIET_MODE=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -q|--quiet)
                QUIET_MODE=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  -q, --quiet    Quiet mode - show only essential progress messages"
                echo "  -h, --help     Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0              # Full verbose output"
                echo "  $0 --quiet      # Quiet mode with minimal output"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Function to print messages based on quiet mode
quiet_print() {
    if [[ "$QUIET_MODE" != "true" ]]; then
        echo "$@"
    fi
}

# Function to print progress messages (always shown)
progress_print() {
    echo "$@"
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    parse_arguments "$@"
    main
fi
