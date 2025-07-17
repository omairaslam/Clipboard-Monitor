#!/bin/bash
set -e  # Exit on any error

# Clipboard Monitor PyInstaller Build Script
# Creates a completely self-contained macOS application bundle

# --- Configuration & Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_NAME="Clipboard Monitor"
BUNDLE_ID="com.clipboardmonitor.app"
VERSION="1.0.0"
BUILD_DIR="build_pyinstaller"
DIST_DIR="dist_pyinstaller"
FINAL_APP_NAME="Clipboard Monitor.app"

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
    
    print_success "Build directories cleaned"
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
    pip install -r requirements.txt

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
    python -m PyInstaller --distpath "$DIST_DIR" --workpath "$BUILD_DIR" main.spec

    if [ ! -d "$DIST_DIR/ClipboardMonitor.app" ]; then
        print_error "Failed to build main service executable"
        exit 1
    fi

    # Build menu bar app executable
    print_status "Building menu bar app executable..."
    python -m PyInstaller --distpath "$DIST_DIR" --workpath "$BUILD_DIR" menu_bar_app.spec
    
    if [ ! -d "$DIST_DIR/ClipboardMonitorMenuBar.app" ]; then
        print_error "Failed to build menu bar app executable"
        exit 1
    fi
    
    print_success "Executables built successfully"
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
        rsync -av --ignore-existing "$DIST_DIR/ClipboardMonitor.app/Contents/Resources/" "$RESOURCES_DIR/"
    fi
    
    # Create the main Info.plist
    create_info_plist "$CONTENTS_DIR/Info.plist"
    
    print_success "App bundle created: $APP_BUNDLE"
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

# Function to update plist templates for bundled executables
update_plist_templates() {
    print_status "Updating plist templates for bundled executables..."
    
    # Create updated plist templates in Resources
    local resources_dir="$FINAL_APP_NAME/Contents/Resources"
    
    # Update main service plist template
    sed "s|/usr/bin/python3|$PWD/$FINAL_APP_NAME/Contents/Resources/Services/ClipboardMonitor|g" \
        plist_files/com.clipboardmonitor.plist > "$resources_dir/com.clipboardmonitor.plist"

    # Update menu bar plist template
    sed "s|/usr/bin/python3|$PWD/$FINAL_APP_NAME/Contents/MacOS/ClipboardMonitorMenuBar|g" \
        plist_files/com.clipboardmonitor.menubar.plist > "$resources_dir/com.clipboardmonitor.menubar.plist"
    
    print_success "Plist templates updated"
}

# Main build process
main() {
    echo "🚀 Starting Clipboard Monitor PyInstaller Build Process"
    echo "======================================================="
    
    # Check if we're in the right directory
    if [ ! -f "main.py" ] || [ ! -f "menu_bar_app.py" ]; then
        print_error "Please run this script from the Clipboard Monitor project root directory"
        exit 1
    fi
    
    clean_build
    activate_venv
    check_dependencies
    build_executables
    create_app_bundle
    update_plist_templates
    
    echo ""
    echo "======================================================="
    print_success "Build completed successfully!"
    echo ""
    echo "📱 Application bundle: $FINAL_APP_NAME"
    echo "📁 Size: $(du -sh "$FINAL_APP_NAME" | cut -f1)"
    echo ""
    echo "🔧 Next steps:"
    echo "  1. Test the application: open '$FINAL_APP_NAME'"
    echo "  2. Create DMG: ./create_dmg.sh"
    echo "  3. Install: Run the install script from within the app"
    echo ""
}

# Run main function
main "$@"
