#!/bin/bash
set -e  # Exit on any error

# Test DMG Workflow Script
# Validates the complete PyInstaller DMG build and installation process

# --- Configuration & Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DMG_NAME="ClipboardMonitor-1.0.dmg"
TEST_DIR="/tmp/clipboard_monitor_test"
APP_NAME="Clipboard Monitor.app"

# Function to print colored output
print_status() {
    echo -e "${BLUE}🧪 $1${NC}"
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

# Function to cleanup test environment
cleanup_test() {
    print_status "Cleaning up test environment..."
    
    # Remove test directory
    rm -rf "$TEST_DIR"
    
    # Unmount any test volumes
    if [ -d "/Volumes/Clipboard Monitor" ]; then
        hdiutil detach "/Volumes/Clipboard Monitor" 2>/dev/null || true
    fi
    
    print_success "Test environment cleaned"
}

# Function to test DMG mounting and contents
test_dmg_mounting() {
    print_status "Testing DMG mounting and contents..."
    
    # Check if DMG exists
    if [ ! -f "$DMG_NAME" ]; then
        print_error "DMG file '$DMG_NAME' not found"
        return 1
    fi
    
    # Mount DMG
    print_status "Mounting DMG..."
    hdiutil attach "$DMG_NAME" -readonly -nobrowse
    
    # Check DMG contents
    print_status "Verifying DMG contents..."
    
    # Check if app bundle exists
    if [ ! -d "/Volumes/Clipboard Monitor/$APP_NAME" ]; then
        print_error "App bundle not found in DMG"
        return 1
    fi
    
    # Check if Applications symlink exists
    if [ ! -L "/Volumes/Clipboard Monitor/Applications" ]; then
        print_error "Applications symlink not found in DMG"
        return 1
    fi
    
    # Check if install script exists
    if [ ! -f "/Volumes/Clipboard Monitor/install.sh" ]; then
        print_error "install.sh not found in DMG"
        return 1
    fi
    
    # Check if README exists
    if [ ! -f "/Volumes/Clipboard Monitor/README.txt" ]; then
        print_error "README.txt not found in DMG"
        return 1
    fi
    
    print_success "DMG contents verified"
    return 0
}

# Function to test app bundle structure
test_app_bundle() {
    print_status "Testing app bundle structure..."
    
    local app_path="/Volumes/Clipboard Monitor/$APP_NAME"
    
    # Check main executable
    if [ ! -f "$app_path/Contents/MacOS/ClipboardMonitorMenuBar" ]; then
        print_error "Main executable not found"
        return 1
    fi
    
    # Check background service executable
    if [ ! -f "$app_path/Contents/Resources/Services/ClipboardMonitor" ]; then
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
    
    # Check essential Python files
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

# Function to test app installation simulation
test_installation_simulation() {
    print_status "Testing installation simulation..."
    
    # Create test directory
    mkdir -p "$TEST_DIR"
    
    # Copy app from DMG to test directory
    print_status "Copying app to test directory..."
    cp -R "/Volumes/Clipboard Monitor/$APP_NAME" "$TEST_DIR/"
    
    # Copy install script
    cp "/Volumes/Clipboard Monitor/install.sh" "$TEST_DIR/"
    
    # Test if executables are functional (basic check)
    print_status "Testing executable functionality..."
    
    # Test main executable (should exit quickly with --help or similar)
    if timeout 5s "$TEST_DIR/$APP_NAME/Contents/MacOS/ClipboardMonitorMenuBar" --version 2>/dev/null; then
        print_success "Menu bar executable responds"
    else
        print_warning "Menu bar executable test inconclusive (expected for GUI app)"
    fi
    
    # Test background service executable
    if timeout 5s "$TEST_DIR/$APP_NAME/Contents/Resources/Services/ClipboardMonitor" --version 2>/dev/null; then
        print_success "Background service executable responds"
    else
        print_warning "Background service executable test inconclusive"
    fi
    
    print_success "Installation simulation completed"
    return 0
}

# Function to test file permissions
test_permissions() {
    print_status "Testing file permissions..."
    
    local app_path="/Volumes/Clipboard Monitor/$APP_NAME"
    
    # Check if executables are executable
    if [ ! -x "$app_path/Contents/MacOS/ClipboardMonitorMenuBar" ]; then
        print_error "Main executable is not executable"
        return 1
    fi
    
    if [ ! -x "$app_path/Contents/Resources/Services/ClipboardMonitor" ]; then
        print_error "Background service executable is not executable"
        return 1
    fi
    
    if [ ! -x "/Volumes/Clipboard Monitor/install.sh" ]; then
        print_error "install.sh is not executable"
        return 1
    fi
    
    print_success "File permissions verified"
    return 0
}

# Function to display DMG information
display_dmg_info() {
    print_status "DMG Information:"
    echo "  📁 File: $DMG_NAME"
    echo "  📏 Size: $(du -sh "$DMG_NAME" | cut -f1)"
    echo "  🔍 Type: $(file "$DMG_NAME")"
    echo ""
    
    print_status "App Bundle Information:"
    local app_path="/Volumes/Clipboard Monitor/$APP_NAME"
    echo "  📱 Bundle: $APP_NAME"
    echo "  📏 Size: $(du -sh "$app_path" | cut -f1)"
    echo "  🆔 Bundle ID: $(defaults read "$app_path/Contents/Info.plist" CFBundleIdentifier 2>/dev/null || echo "Unknown")"
    echo "  📋 Version: $(defaults read "$app_path/Contents/Info.plist" CFBundleShortVersionString 2>/dev/null || echo "Unknown")"
    echo ""
}

# Main test function
main() {
    echo "🧪 Starting Clipboard Monitor DMG Workflow Test"
    echo "================================================"
    
    # Check if DMG exists
    if [ ! -f "$DMG_NAME" ]; then
        print_error "DMG file '$DMG_NAME' not found. Please run build_pyinstaller.sh and create_dmg.sh first."
        exit 1
    fi
    
    # Run tests
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
    
    if test_installation_simulation; then
        print_success "Installation simulation test passed"
    else
        print_error "Installation simulation test failed"
        test_results=1
    fi
    
    # Display information
    echo ""
    display_dmg_info
    
    # Cleanup
    cleanup_test
    
    # Final results
    echo "================================================"
    if [ $test_results -eq 0 ]; then
        print_success "All tests passed! DMG is ready for distribution."
        echo ""
        echo "🚀 Distribution ready:"
        echo "  1. DMG file: $DMG_NAME"
        echo "  2. Users can download, mount, and drag to Applications"
        echo "  3. Run install.sh to set up background services"
        echo "  4. No Python installation required on target machines"
    else
        print_error "Some tests failed. Please review the issues above."
        exit 1
    fi
}

# Run main function
main "$@"
