#!/bin/bash
set -e

# Unified Build, Create, and Install PKG Script
# Combines PyInstaller build with PKG creation and installation

# Import existing build functions from build_create_install_dmg.sh
source build_create_install_dmg.sh

# Color definitions for quiet mode
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Additional quiet mode helper functions
quiet_status() {
    if [[ "$QUIET_MODE" == "true" ]]; then
        echo -e "${BLUE}📦 $1${NC}"
    else
        print_status "$1"
    fi
}

quiet_success() {
    if [[ "$QUIET_MODE" == "true" ]]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        print_success "$1"
    fi
}

quiet_error() {
    if [[ "$QUIET_MODE" == "true" ]]; then
        echo -e "${RED}❌ $1${NC}"
    else
        print_error "$1"
    fi
}

# PKG-specific configuration
PKG_NAME="ClipboardMonitor-1.0.pkg"
TEST_DIR="/tmp/clipboard_monitor_pkg_test"

# Function to test PKG integrity
test_pkg_integrity() {
    quiet_status "Testing PKG integrity..."

    if [ ! -f "$PKG_NAME" ]; then
        quiet_error "PKG file not found: $PKG_NAME"
        return 1
    fi

    # Test PKG structure
    if pkgutil --check-signature "$PKG_NAME" > /dev/null 2>&1; then
        quiet_success "PKG signature check passed"
    else
        quiet_status "PKG signature check skipped (unsigned)"
    fi

    # Test PKG contents
    if pkgutil --payload-files "$PKG_NAME" > /dev/null 2>&1; then
        quiet_success "PKG payload structure valid"
    else
        quiet_error "PKG payload structure invalid"
        return 1
    fi

    quiet_success "PKG integrity test passed"
    return 0
}

# Function to verify PKG installation
verify_pkg_installation() {
    quiet_status "Verifying PKG installation..."
    local verification_passed=true

    local app_in_apps="/Applications/Clipboard Monitor.app"

    # Verify app exists
    if [ -d "$app_in_apps" ]; then
        quiet_success "Found app in /Applications"
    else
        quiet_error "App not found in /Applications"
        verification_passed=false
    fi

    # Verify app bundle structure
    if [ -f "$app_in_apps/Contents/MacOS/ClipboardMonitorMenuBar" ]; then
        quiet_success "App bundle structure valid"
    else
        quiet_error "App bundle structure invalid"
        verification_passed=false
    fi

    # Verify services are running (more reliable than checking plist files)
    local bg_running=$(ps aux | grep -E "ClipboardMonitor\.app.*ClipboardMonitor$" | grep -v grep | wc -l)
    local mb_running=$(ps aux | grep -E "ClipboardMonitorMenuBar$" | grep -v grep | wc -l)

    if [[ "$bg_running" -gt 0 ]]; then
        quiet_success "Background service is running"
    else
        quiet_error "Background service not running"
        verification_passed=false
    fi

    if [[ "$mb_running" -gt 0 ]]; then
        quiet_success "Menu bar service is running"
    else
        quiet_error "Menu bar service not running"
        verification_passed=false
    fi

    if [ "$verification_passed" = true ]; then
        quiet_success "PKG installation verification passed"
        return 0
    else
        quiet_error "PKG installation verification failed"
        return 1
    fi
}

# Function to check service status
check_service_status() {
    quiet_status "Checking service status..."

    # Wait a moment for services to start
    sleep 3

    # Check using process list instead of launchctl to avoid permission issues
    local bg_running=$(ps aux | grep -E "ClipboardMonitor\.app.*ClipboardMonitor$" | grep -v grep | wc -l)
    local mb_running=$(ps aux | grep -E "ClipboardMonitorMenuBar$" | grep -v grep | wc -l)

    if [[ "$bg_running" -gt 0 ]]; then
        quiet_success "Background service is running"
    else
        if [[ "$QUIET_MODE" == "true" ]]; then
            echo -e "${YELLOW}⚠️  Background service not detected${NC}"
        else
            print_warning "Background service not detected"
        fi
    fi

    if [[ "$mb_running" -gt 0 ]]; then
        quiet_success "Menu bar service is running"
    else
        if [[ "$QUIET_MODE" == "true" ]]; then
            echo -e "${YELLOW}⚠️  Menu bar service not detected${NC}"
        else
            print_warning "Menu bar service not detected"
        fi
    fi

    if [[ "$bg_running" -gt 0 && "$mb_running" -gt 0 ]]; then
        quiet_success "All services are running! Check your menu bar for the 📋 icon."
        return 0
    else
        if [[ "$QUIET_MODE" == "true" ]]; then
            echo -e "${YELLOW}⚠️  Some services may not be running correctly${NC}"
        else
            print_warning "Some services may not be running correctly. Check logs or try restarting."
        fi
        return 1
    fi
}

# Function to handle PKG installation errors
handle_installation_error() {
    if [[ "$QUIET_MODE" != "true" ]]; then
        print_error "PKG installation failed. Attempting cleanup..."
    fi

    # Stop any partially started services
    launchctl unload "$HOME/Library/LaunchAgents/com.clipboardmonitor.plist" 2>/dev/null || true
    launchctl unload "$HOME/Library/LaunchAgents/com.clipboardmonitor.menubar.plist" 2>/dev/null || true

    # Remove partially installed files
    rm -f "$HOME/Library/LaunchAgents/com.clipboardmonitor.plist" 2>/dev/null || true
    rm -f "$HOME/Library/LaunchAgents/com.clipboardmonitor.menubar.plist" 2>/dev/null || true

    # Note: We don't remove the app from /Applications as user might want to keep it
    if [[ "$QUIET_MODE" != "true" ]]; then
        print_warning "Partial cleanup completed. You may need to manually remove the app from /Applications"
    fi
}

# Function to cleanup test environment
cleanup_pkg_test() {
    if [ -d "$TEST_DIR" ]; then
        rm -rf "$TEST_DIR"
    fi
}

# Function to verify PKG was created successfully
verify_pkg_creation() {
    if [ ! -f "$PKG_NAME" ]; then
        quiet_error "PKG file was not created: $PKG_NAME"
        return 1
    fi

    local pkg_size=$(stat -f%z "$PKG_NAME" 2>/dev/null || echo "0")
    if [ "$pkg_size" -lt 1000 ]; then
        quiet_error "PKG file appears to be empty or corrupted"
        return 1
    fi

    quiet_success "PKG file created successfully ($(du -sh "$PKG_NAME" | cut -f1))"
    return 0
}

# Function to verify installation success by checking actual results
verify_installation_success() {
    # Check if app was installed
    if [ ! -d "/Applications/Clipboard Monitor.app" ]; then
        return 1
    fi

    # Wait longer for services to start and check multiple times
    local max_attempts=6
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        sleep 2
        local bg_running=$(ps aux | grep -E "ClipboardMonitor\.app.*ClipboardMonitor$" | grep -v grep | wc -l)
        local mb_running=$(ps aux | grep -E "ClipboardMonitorMenuBar$" | grep -v grep | wc -l)

        if [[ "$bg_running" -gt 0 && "$mb_running" -gt 0 ]]; then
            return 0
        fi

        if [[ "$QUIET_MODE" != "true" ]]; then
            echo "Waiting for services to start... (attempt $attempt/$max_attempts)"
        fi

        attempt=$((attempt + 1))
    done

    return 1
}

# Override DMG creation with PKG creation and installation
create_and_install_pkg() {
    quiet_status "Creating PKG installer..."

    # Export QUIET_MODE so create_pkg.sh can use it
    export QUIET_MODE

    # Use the create_pkg.sh functionality
    ./create_pkg.sh

    # Verify PKG creation
    if ! verify_pkg_creation; then
        quiet_error "PKG creation failed! Aborting installation."
        return 1
    fi

    quiet_success "PKG installer created successfully!"

    # Install the PKG automatically
    quiet_status "Installing PKG on local machine..."
    if [[ "$QUIET_MODE" != "true" ]]; then
        print_status "You will be prompted for your password to install the PKG..."
    fi

    # Try installation with better error handling
    local install_result=0
    if [[ "$QUIET_MODE" == "true" ]]; then
        # Note: The installer may show a "Terminated: 15" message after completion
        # This is normal behavior and indicates successful installation
        sudo installer -pkg "$PKG_NAME" -target / >/dev/null 2>&1 || install_result=$?
    else
        sudo installer -pkg "$PKG_NAME" -target / || install_result=$?
    fi

    # Show progress message in quiet mode
    if [[ "$QUIET_MODE" == "true" ]]; then
        quiet_status "Verifying installation and starting services..."
    fi

    # The installer often returns 143 (SIGTERM) even on successful installation
    # So we need to verify actual success by checking the results
    if verify_installation_success; then
        quiet_success "PKG installed and services started successfully!"
        return 0
    else
        # Only show detailed error info if not in quiet mode
        if [[ "$QUIET_MODE" != "true" ]]; then
            print_error "PKG installation verification failed (installer exit code: $install_result)"

            # Check if it was a permission/authentication issue
            if [ $install_result -eq 1 ]; then
                print_error "Authentication failed or permission denied"
            elif [ $install_result -eq 143 ]; then
                print_warning "Installer was terminated but this may be normal - checking actual results..."
            fi
        else
            quiet_error "PKG installation failed - services not running"
        fi

        handle_installation_error
        return 1
    fi
}

# Function to display PKG info
display_pkg_info() {
    if [[ "$QUIET_MODE" != "true" ]]; then
        echo ""
        echo -e "${BLUE}📦 PKG Information:${NC}"
        echo "  • File: $PKG_NAME"
        echo "  • Size: $(du -sh "$PKG_NAME" | cut -f1)"
        echo "  • Identifier: com.clipboardmonitor.installer"
        echo "  • Version: 1.0.0"
        echo ""
    fi
}

# Main function override
main() {
    if [[ "$QUIET_MODE" == "true" ]]; then
        print_header "🚀 Clipboard Monitor - Quiet PKG Build"
        echo ""
        echo -e "${BLUE}Running in quiet mode - showing only essential progress...${NC}"
        echo ""
    else
        print_header "🚀 Unified Build, Create, and Install PKG Workflow"
        echo ""
        echo "This script will:"
        echo "  1. 🔨 Build PyInstaller executables"
        echo "  2. 📦 Create unified app bundle"
        echo "  3. 🎁 Generate PKG installer"
        echo "  4. 🧪 Test PKG integrity"
        echo "  5. 💾 Install PKG locally"
        echo "  6. ✅ Verify installation and services"
        echo ""
    fi
    
    # Phase 1: Build (same as before)
    print_header "Phase 1: Building Executables"
    clean_build
    activate_venv
    check_dependencies
    build_executables
    create_app_bundle
    update_plist_templates
    quiet_success "Build phase completed successfully!"
    if [[ "$QUIET_MODE" != "true" ]]; then
        echo ""
    fi
    
    # Phase 2: Create PKG
    print_header "Phase 2: Creating PKG Installer"
    if ! create_and_install_pkg; then
        quiet_error "PKG creation or installation failed!"
        cleanup_pkg_test
        exit 1
    fi

    quiet_success "PKG creation and installation phase completed successfully!"
    if [[ "$QUIET_MODE" != "true" ]]; then
        echo ""
    fi
    
    # Phase 3: Test PKG
    print_header "Phase 3: Testing PKG"
    local test_results=0

    cleanup_pkg_test

    if test_pkg_integrity; then
        # Success message already printed by test_pkg_integrity function
        true
    else
        quiet_error "PKG integrity test failed"
        test_results=1
    fi

    if verify_pkg_installation; then
        # Success message already printed by verify_pkg_installation function
        true
    else
        quiet_error "PKG installation verification failed"
        test_results=1
    fi

    if check_service_status; then
        # Success message already printed by check_service_status function
        true
    else
        quiet_error "Service status check failed"
        test_results=1
    fi
    
    # Display information
    display_pkg_info
    
    # Final results
    print_header "🎉 Workflow Complete!"
    if [ $test_results -eq 0 ]; then
        quiet_success "All tests passed! PKG installation successful."
        if [[ "$QUIET_MODE" != "true" ]]; then
            echo ""
            echo "📁 Generated files:"
            echo "  • ${PKG_NAME} (PKG installer)"
            echo "  • Clipboard Monitor.app (Installed in /Applications)"
            echo ""
            echo "🚀 Services Status:"
            echo "  • Background Monitor: Running"
            echo "  • Menu Bar App: Running (check menu bar for 📋 icon)"
            echo ""
        else
            echo ""
            echo "📋 Clipboard Monitor is now running! Check your menu bar for the clipboard icon."
        fi
    else
        quiet_error "Some tests failed. Please review the issues above."
        cleanup_pkg_test
        exit 1
    fi

    cleanup_pkg_test
    if [[ "$QUIET_MODE" != "true" ]]; then
        print_success "Build, PKG creation, installation, and verification completed!"
    fi
}

# Function to parse command line arguments (same as DMG version)
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

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    parse_arguments "$@"
    main
fi
