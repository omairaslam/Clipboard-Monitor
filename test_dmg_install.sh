#!/bin/bash

# Clipboard Monitor DMG Testing Script
# This script automates the complete testing workflow for the DMG

set -e  # Exit on any error

# Check if running in auto mode (for debugging)
AUTO_MODE=${1:-""}
if [[ "$AUTO_MODE" == "--auto" ]]; then
    echo "🤖 Running in automatic mode (no prompts)"
fi

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

    # Auto mode - skip prompts
    if [[ "$AUTO_MODE" == "--auto" ]]; then
        echo "🤖 Auto mode: Proceeding automatically"
        return 0
    fi

    # Interactive mode - ask for confirmation
    local response
    while true; do
        echo -n "Continue? (Y/n): "
        read -r response

        # Default to yes if empty response
        if [[ -z "$response" ]]; then
            response="y"
        fi

        # Convert to lowercase for comparison
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
                echo "Please enter 'y' for yes or 'n' for no. (Default: yes)"
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
    
    # Wait for mount to complete
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
            # Make sure it's executable
            chmod +x "$MOUNT_POINT/uninstall.sh"
            
            # Run uninstall script (it will ask for its own confirmation)
            "$MOUNT_POINT/uninstall.sh" || true  # Don't fail if uninstall has issues
            
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
        
        # Remove existing app if it exists
        if [ -d "$APPLICATIONS_DIR/$APP_NAME" ]; then
            print_warning "Removing existing app from Applications"
            rm -rf "$APPLICATIONS_DIR/$APP_NAME"
        fi
        
        # Copy new app
        cp -R "$MOUNT_POINT/$APP_NAME" "$APPLICATIONS_DIR/"
        
        print_success "App copied to Applications"
    fi
}

# Function to copy plist files
copy_plist_files() {
    if ask_permission "Copy plist files to LaunchAgents folder"; then
        print_step "Preparing for manual plist file copying..."

        # Create LaunchAgents directory if it doesn't exist
        mkdir -p "$LAUNCH_AGENTS_DIR"

        # Check if plist files exist in DMG
        local plist_files_found=0
        local plist_list=""

        for plist_file in "$MOUNT_POINT"/*.plist; do
            if [ -f "$plist_file" ]; then
                local filename=$(basename "$plist_file")
                plist_list="$plist_list\n  • $filename"
                plist_files_found=1
            fi
        done

        if [ $plist_files_found -eq 0 ]; then
            print_warning "No plist files found in DMG"
            return
        fi

        print_info "Found plist files to copy:$plist_list"
        echo ""
        print_step "Opening folders for manual copying..."

        # Open the DMG folder (source)
        open "$MOUNT_POINT"
        sleep 1

        # Open the LaunchAgents folder (destination)
        open "$LAUNCH_AGENTS_DIR"
        sleep 1

        print_info "📁 Two Finder windows should now be open:"
        print_info "   1. DMG folder (source) - contains the .plist files"
        print_info "   2. LaunchAgents folder (destination) - where to copy them"
        echo ""
        print_step "Please manually copy the .plist files from DMG to LaunchAgents folder"

        # Wait for user confirmation
        local response
        while true; do
            echo -n "Have you copied the plist files? (Y/n): "
            read -r response

            # Default to yes if empty response
            if [[ -z "$response" ]]; then
                response="y"
            fi

            response=$(echo "$response" | tr '[:upper:]' '[:lower:]')

            case "$response" in
                y|yes)
                    print_success "Plist files copying completed"
                    break
                    ;;
                n|no)
                    print_warning "Please copy the plist files before continuing"
                    ;;
                *)
                    echo "Please enter 'y' for yes or 'n' for no. (Default: yes)"
                    ;;
            esac
        done
    fi
}

# Function to run install script
run_install() {
    print_warning "⚠️  WARNING: The install script will start clipboard monitor services"
    print_warning "   This may cause VS Code to crash or become unresponsive"
    print_warning "   Consider running this step manually outside of VS Code"

    if ask_permission "Run install.sh script to complete installation (may crash VS Code)"; then
        print_step "Running install script..."

        if [ -f "$MOUNT_POINT/install.sh" ]; then
            # Make sure it's executable
            chmod +x "$MOUNT_POINT/install.sh"

            print_warning "🚨 Starting install script - VS Code may crash in 3 seconds..."
            sleep 3

            # Run install script
            "$MOUNT_POINT/install.sh"

            print_success "Install script completed"
        else
            print_error "Install script not found in DMG"
            exit 1
        fi
    else
        print_info "💡 To complete installation manually:"
        print_info "   1. Open Terminal outside VS Code"
        print_info "   2. Run: $MOUNT_POINT/install.sh"
        print_info "   3. Or copy plist files and load them manually"
    fi
}

# Function to show final status
show_final_status() {
    echo -e "\n${GREEN}🎉 DMG Testing Workflow Complete!${NC}"
    echo -e "\n${BLUE}📊 Installation Status:${NC}"
    
    # Check if app is in Applications
    if [ -d "$APPLICATIONS_DIR/$APP_NAME" ]; then
        print_success "App installed in Applications"
    else
        print_warning "App not found in Applications"
    fi
    
    # Check if plist files are installed
    local plist_count=$(ls "$LAUNCH_AGENTS_DIR"/com.clipboardmonitor*.plist 2>/dev/null | wc -l)
    if [ $plist_count -gt 0 ]; then
        print_success "Found $plist_count plist file(s) in LaunchAgents"
    else
        print_warning "No clipboard monitor plist files found in LaunchAgents"
    fi
    
    # Check if processes are running
    local running_processes=$(ps aux | grep -i clipboard | grep -v grep | wc -l)
    if [ $running_processes -gt 0 ]; then
        print_success "Found $running_processes clipboard monitor process(es) running"
    else
        print_warning "No clipboard monitor processes currently running"
    fi
    
    echo -e "\n${BLUE}🔧 Next Steps:${NC}"
    echo "1. Check menu bar for clipboard monitor icon"
    echo "2. Open http://localhost:8001 to view dashboard"
    echo "3. Test clipboard functionality"

    if [ $running_processes -gt 0 ]; then
        echo -e "\n${YELLOW}⚠️  Note: If VS Code crashed during installation, this is expected${NC}"
        echo -e "${YELLOW}   The clipboard monitor services can interfere with VS Code${NC}"
        echo -e "${YELLOW}   You can restart VS Code now - the services are running independently${NC}"
    fi
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
    echo -e "${BLUE}🚀 Clipboard Monitor DMG Testing Script${NC}"
    echo -e "${BLUE}======================================${NC}"
    
    # Step 1: Check if DMG exists
    check_dmg_exists
    
    # Step 2: Cleanup any existing mounts
    cleanup_existing_mount
    
    # Step 3: Mount DMG
    if ask_permission "Mount the DMG file"; then
        mount_dmg
    else
        print_error "Cannot proceed without mounting DMG"
        exit 1
    fi
    
    # Step 4: Run uninstall script
    run_uninstall
    
    # Step 5: Copy app to Applications
    copy_app_to_applications
    
    # Step 6: Copy plist files
    copy_plist_files
    
    # Step 7: Run install script
    run_install
    
    # Step 8: Show final status
    show_final_status
}

# Run main function
main "$@"
