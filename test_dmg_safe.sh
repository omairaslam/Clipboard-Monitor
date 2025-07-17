#!/bin/bash

# Clipboard Monitor DMG Safe Testing Script
# This script tests the DMG without running the install script (VS Code safe)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DMG_NAME="ClipboardMonitor-1.0.dmg"
APP_NAME="Clipboard Monitor.app"
MOUNT_POINT="/Volumes/Clipboard Monitor"
APPLICATIONS_DIR="/Applications"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

# Function to print colored output
print_step() {
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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to ask for user confirmation
ask_permission() {
    local step_description="$1"
    echo -e "\n${YELLOW}🤔 Ready to: $step_description${NC}"
    
    local response
    while true; do
        echo -n "Continue? (y/n): "
        read -r response
        
        response=$(echo "$response" | tr '[:upper:]' '[:lower:]')
        
        case "$response" in
            y|yes)
                return 0
                ;;
            n|no)
                print_warning "Step skipped by user"
                return 1
                ;;
            *)
                echo "Please enter 'y' for yes or 'n' for no."
                ;;
        esac
    done
}

# Function to check if DMG exists
check_dmg_exists() {
    if [ ! -f "$DMG_NAME" ]; then
        print_error "DMG file '$DMG_NAME' not found in current directory"
        echo "Current directory: $(pwd)"
        echo "Available files:"
        ls -la *.dmg 2>/dev/null || echo "No DMG files found"
        exit 1
    fi
    print_success "Found DMG: $DMG_NAME"
}

# Function to unmount any existing DMG
cleanup_existing_mount() {
    if [ -d "$MOUNT_POINT" ]; then
        print_warning "DMG already mounted, unmounting..."
        hdiutil detach "$MOUNT_POINT" 2>/dev/null || true
        sleep 2
    fi
}

# Function to mount DMG
mount_dmg() {
    print_step "Mounting DMG: $DMG_NAME"
    hdiutil attach "$DMG_NAME" -quiet
    
    sleep 3
    
    if [ ! -d "$MOUNT_POINT" ]; then
        print_error "Failed to mount DMG"
        exit 1
    fi
    
    print_success "DMG mounted at: $MOUNT_POINT"
    echo "Contents:"
    ls -la "$MOUNT_POINT/"
}

# Function to run uninstall script
run_uninstall() {
    if ask_permission "Run uninstall script to clean up any existing installation"; then
        print_step "Running uninstall script..."
        
        if [ -f "$MOUNT_POINT/uninstall.sh" ]; then
            chmod +x "$MOUNT_POINT/uninstall.sh"
            "$MOUNT_POINT/uninstall.sh" || true
            print_success "Uninstall script completed"
        else
            print_warning "Uninstall script not found in DMG"
        fi
    fi
}

# Function to copy app to Applications
copy_app_to_applications() {
    if ask_permission "Copy '$APP_NAME' to Applications folder"; then
        print_step "Copying app to Applications..."
        
        if [ ! -d "$MOUNT_POINT/$APP_NAME" ]; then
            print_error "App not found in DMG: $MOUNT_POINT/$APP_NAME"
            exit 1
        fi
        
        if [ -d "$APPLICATIONS_DIR/$APP_NAME" ]; then
            print_warning "Removing existing app from Applications"
            rm -rf "$APPLICATIONS_DIR/$APP_NAME"
        fi
        
        cp -R "$MOUNT_POINT/$APP_NAME" "$APPLICATIONS_DIR/"
        print_success "App copied to Applications"
    fi
}

# Function to copy plist files
copy_plist_files() {
    if ask_permission "Copy plist files to LaunchAgents folder"; then
        print_step "Copying plist files..."
        
        mkdir -p "$LAUNCH_AGENTS_DIR"
        
        local plist_files_found=0
        
        for plist_file in "$MOUNT_POINT"/*.plist; do
            if [ -f "$plist_file" ]; then
                local filename=$(basename "$plist_file")
                print_step "Copying $filename to LaunchAgents"
                cp "$plist_file" "$LAUNCH_AGENTS_DIR/"
                plist_files_found=1
            fi
        done
        
        if [ $plist_files_found -eq 0 ]; then
            print_warning "No plist files found in DMG"
        else
            print_success "Plist files copied to LaunchAgents"
        fi
    fi
}

# Function to show final status
show_final_status() {
    echo -e "\n${GREEN}🎉 Safe DMG Testing Complete!${NC}"
    echo -e "\n${BLUE}📊 Installation Status:${NC}"
    
    if [ -d "$APPLICATIONS_DIR/$APP_NAME" ]; then
        print_success "App installed in Applications"
    else
        print_warning "App not found in Applications"
    fi
    
    local plist_count=$(ls "$LAUNCH_AGENTS_DIR"/com.clipboardmonitor*.plist 2>/dev/null | wc -l)
    if [ $plist_count -gt 0 ]; then
        print_success "Found $plist_count plist file(s) in LaunchAgents"
    else
        print_warning "No clipboard monitor plist files found in LaunchAgents"
    fi
    
    echo -e "\n${BLUE}🔧 To Complete Installation:${NC}"
    echo "1. Run the install script manually: $MOUNT_POINT/install.sh"
    echo "2. Or load the plist files manually with launchctl"
    echo "3. Check menu bar for clipboard monitor icon after loading"
    
    echo -e "\n${GREEN}✅ VS Code Safe: Install script was NOT run${NC}"
    echo -e "${GREEN}   No services started, VS Code should remain stable${NC}"
}

# Function to cleanup on exit
cleanup() {
    if [ -d "$MOUNT_POINT" ]; then
        print_step "Cleaning up: Unmounting DMG"
        hdiutil detach "$MOUNT_POINT" 2>/dev/null || true
    fi
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    echo -e "${BLUE}🚀 Clipboard Monitor Safe DMG Testing Script${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo -e "${GREEN}✅ VS Code Safe: Will NOT run install script${NC}"
    echo ""
    
    check_dmg_exists
    cleanup_existing_mount
    
    if ask_permission "Mount the DMG file"; then
        mount_dmg
    else
        print_error "Cannot proceed without mounting DMG"
        exit 1
    fi
    
    run_uninstall
    copy_app_to_applications
    copy_plist_files
    
    show_final_status
}

# Run main function
main "$@"
