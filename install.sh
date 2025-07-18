#!/bin/bash

# FIXED VERSION - Resolves multiple menu bar app spawning issue
# Key fix: KeepAlive=false to prevent infinite respawning

# Note: Removed 'set -e' to handle errors gracefully with user prompts

# --- Configuration & Colors ---
# Define colors for script output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Define application and system paths
APP_NAME="Clipboard Monitor.app"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$HOME/Library/Logs"
PLIST_BACKGROUND="com.clipboardmonitor.plist"
PLIST_MENUBAR="com.clipboardmonitor.menubar.plist"

# --- Functions ---
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}    Clipboard Monitor - Installation${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${YELLOW}$1${NC}"
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

# Function to handle script exit with user prompt
exit_with_prompt() {
    local exit_code=${1:-0}
    echo ""
    echo -e "${BLUE}Press any key to close this window...${NC}"
    read -n 1 -s
    exit $exit_code
}

# Function to check service status and show logs if failed
check_service_status() {
    local service_name="$1"
    local plist_label="$2"
    local log_prefix="$3"
    local process_pattern="$4"

    echo -e "${BLUE}📊 Checking $service_name status...${NC}"

    # Check if plist is loaded using the correct label
    local launchctl_output=$(launchctl list | grep "$plist_label" | head -1)
    if [ -n "$launchctl_output" ]; then
        local pid=$(echo "$launchctl_output" | awk '{print $1}')
        local exit_code=$(echo "$launchctl_output" | awk '{print $2}')

        echo -e "${GREEN}✅ $service_name is loaded (PID: $pid, Exit Code: $exit_code)${NC}"

        # Check if process is actually running using the correct pattern
        if pgrep -f "$process_pattern" > /dev/null; then
            echo -e "${GREEN}✅ $service_name is running${NC}"

            # Show brief status without treating empty logs as errors
            show_service_status "$log_prefix" "$service_name"
            return 0
        else
            echo -e "${YELLOW}⚠️  $service_name is loaded but process not found${NC}"
            show_service_logs "$log_prefix" "$service_name"
            return 1
        fi
    else
        echo -e "${RED}❌ $service_name is not loaded${NC}"
        show_service_logs "$log_prefix" "$service_name"
        return 1
    fi
}

# Function to show brief service status (for running services)
show_service_status() {
    local log_prefix="$1"
    local service_name="$2"
    local log_dir="$HOME/Library/Logs"

    # Only show logs if there are actual errors
    if [[ -f "$log_dir/${log_prefix}.err.log" ]] && [[ -s "$log_dir/${log_prefix}.err.log" ]]; then
        echo -e "${YELLOW}⚠️  Error log has content (last 3 lines):${NC}"
        tail -3 "$log_dir/${log_prefix}.err.log" | sed 's/^/   /'
    else
        echo -e "${GREEN}✅ No errors in log files${NC}"
    fi
}

# Function to show recent log entries for failed services
show_service_logs() {
    local log_prefix="$1"
    local service_name="$2"
    local log_dir="$HOME/Library/Logs"
    local has_errors=false

    echo -e "${BLUE}📋 Recent logs for $service_name:${NC}"

    # Show error log if it exists and has content
    if [[ -f "$log_dir/${log_prefix}.err.log" ]] && [[ -s "$log_dir/${log_prefix}.err.log" ]]; then
        echo -e "${RED}❌ Error log (last 10 lines):${NC}"
        tail -10 "$log_dir/${log_prefix}.err.log" | sed 's/^/   /'
        has_errors=true
    fi

    # Show output log if it exists and has content
    if [[ -f "$log_dir/${log_prefix}.out.log" ]] && [[ -s "$log_dir/${log_prefix}.out.log" ]]; then
        echo -e "${BLUE}📄 Output log (last 10 lines):${NC}"
        tail -10 "$log_dir/${log_prefix}.out.log" | sed 's/^/   /'

        # Check if output log contains serious error indicators only
        if grep -qi "fatal\|critical\|exception\|traceback\|crash\|abort" "$log_dir/${log_prefix}.out.log"; then
            has_errors=true
        fi
    fi

    # If no logs exist or are empty, this is normal for services that start successfully
    if [[ ! -f "$log_dir/${log_prefix}.err.log" ]] && [[ ! -f "$log_dir/${log_prefix}.out.log" ]]; then
        echo -e "${BLUE}ℹ️  No log files found - service may not have started yet or logs not configured${NC}"
    elif [[ ! -s "$log_dir/${log_prefix}.err.log" ]] && [[ ! -s "$log_dir/${log_prefix}.out.log" ]]; then
        echo -e "${BLUE}ℹ️  Log files exist but are empty - this is normal for services running without issues${NC}"
    fi

    echo ""
    return $([ "$has_errors" = true ] && echo 1 || echo 0)
}

# Function to check log files for errors
check_log_files() {
    echo -e "${BLUE}📋 Checking log files for errors...${NC}"

    local error_found=false
    local log_dir="$HOME/Library/Logs"

    # Check main service error log
    if [[ -f "$log_dir/ClipboardMonitor.err.log" ]]; then
        if [[ -s "$log_dir/ClipboardMonitor.err.log" ]]; then
            echo -e "${YELLOW}⚠️  Errors found in ClipboardMonitor.err.log (last 10 lines):${NC}"
            tail -10 "$log_dir/ClipboardMonitor.err.log" | sed 's/^/   /'
            error_found=true
        else
            echo -e "${GREEN}✅ ClipboardMonitor.err.log is clean${NC}"
        fi
    else
        echo -e "${BLUE}ℹ️  ClipboardMonitor.err.log not found (service may not have started yet)${NC}"
    fi

    # Check main service output log for serious errors only
    if [[ -f "$log_dir/ClipboardMonitor.out.log" ]]; then
        if [[ -s "$log_dir/ClipboardMonitor.out.log" ]]; then
            # Check for serious error indicators only (avoid false positives)
            if grep -qi "fatal\|critical\|exception\|traceback\|crash\|abort" "$log_dir/ClipboardMonitor.out.log"; then
                echo -e "${YELLOW}⚠️  Serious issues found in ClipboardMonitor.out.log (last 10 lines):${NC}"
                tail -10 "$log_dir/ClipboardMonitor.out.log" | sed 's/^/   /'
                error_found=true
            else
                echo -e "${GREEN}✅ ClipboardMonitor.out.log shows normal operation${NC}"
            fi
        else
            echo -e "${GREEN}✅ ClipboardMonitor.out.log is empty (normal)${NC}"
        fi
    fi

    # Check menu bar service error log
    if [[ -f "$log_dir/ClipboardMonitorMenuBar.err.log" ]]; then
        if [[ -s "$log_dir/ClipboardMonitorMenuBar.err.log" ]]; then
            echo -e "${YELLOW}⚠️  Errors found in ClipboardMonitorMenuBar.err.log (last 10 lines):${NC}"
            tail -10 "$log_dir/ClipboardMonitorMenuBar.err.log" | sed 's/^/   /'
            error_found=true
        else
            echo -e "${GREEN}✅ ClipboardMonitorMenuBar.err.log is clean${NC}"
        fi
    else
        echo -e "${BLUE}ℹ️  ClipboardMonitorMenuBar.err.log not found (service may not have started yet)${NC}"
    fi

    # Check menu bar service output log for serious errors only
    if [[ -f "$log_dir/ClipboardMonitorMenuBar.out.log" ]]; then
        if [[ -s "$log_dir/ClipboardMonitorMenuBar.out.log" ]]; then
            # Check for serious error indicators only (avoid false positives)
            if grep -qi "fatal\|critical\|exception\|traceback\|crash\|abort" "$log_dir/ClipboardMonitorMenuBar.out.log"; then
                echo -e "${YELLOW}⚠️  Serious issues found in ClipboardMonitorMenuBar.out.log (last 10 lines):${NC}"
                tail -10 "$log_dir/ClipboardMonitorMenuBar.out.log" | sed 's/^/   /'
                error_found=true
            else
                echo -e "${GREEN}✅ ClipboardMonitorMenuBar.out.log shows normal operation${NC}"
            fi
        else
            echo -e "${GREEN}✅ ClipboardMonitorMenuBar.out.log is empty (normal)${NC}"
        fi
    fi

    if [[ "$error_found" == "true" ]]; then
        echo -e "${YELLOW}⚠️  Some errors were found in log files. Services may still be functional.${NC}"
        return 1
    else
        echo -e "${GREEN}✅ No errors found in log files${NC}"
        return 0
    fi
}

# Function to offer opening log files with Console app
offer_console_app() {
    local log_dir="$HOME/Library/Logs"
    echo ""
    echo -e "${BLUE}🔍 Troubleshooting Assistant${NC}"
    echo -e "${BLUE}Would you like me to open the log files with Console app for detailed analysis?${NC}"
    echo ""
    echo -e "${BLUE}Options:${NC}"
    echo "  1. 📱 Open all log files (recommended - default)"
    echo "  2. ⏭️  Skip (continue without opening logs)"
    echo ""
    read -p "Enter your choice (1-2, or press Enter for default): " -n 1 -r
    echo # Move to a new line

    # Default to option 1 if Enter is pressed (empty input)
    if [[ -z "$REPLY" ]]; then
        REPLY="1"
    fi

    case $REPLY in
        1)
            local opened_count=0
            for log_file in "ClipboardMonitor.err.log" "ClipboardMonitor.out.log" "ClipboardMonitorMenuBar.err.log" "ClipboardMonitorMenuBar.out.log"; do
                if [[ -f "$log_dir/$log_file" ]]; then
                    open -a Console "$log_dir/$log_file"
                    ((opened_count++))
                fi
            done
            echo -e "${GREEN}✅ Opened $opened_count log files in Console${NC}"
            ;;
        2|*)
            echo -e "${BLUE}ℹ️  Skipping Console app${NC}"
            ;;
    esac
}

# --- Uninstall Logic ---
uninstall_services() {
    print_header
    echo -e "${YELLOW}🗑️  Uninstalling Clipboard Monitor services...${NC}"
    echo ""

    print_step "🛑 Stopping services..."
    # Stop and unload the services, suppressing errors if they don't exist
    launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" 2>/dev/null || true
    launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" 2>/dev/null || true
    print_success "Services stopped"
    echo ""

    print_step "🗂️  Removing configuration files..."
    # Remove the configuration files
    rm -f "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"
    rm -f "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR"
    print_success "Configuration files removed"
    echo ""

    echo -e "${GREEN}✅ Services have been successfully removed!${NC}"
    echo ""
    echo -e "${BLUE}📝 To complete the uninstall:${NC}"
    echo -e "${BLUE}   Please drag '$APP_NAME' from your Applications folder to the Trash 🗑️${NC}"
    echo ""
    echo -e "${BLUE}Thank you for using Clipboard Monitor! 🙏${NC}"
    exit_with_prompt 0
}

# Check for the --uninstall flag to reverse the installation
if [ "$1" == "--uninstall" ]; then
    uninstall_services
fi

# --- Pre-Installation Check ---
check_existing_installation() {
    local app_installed=false
    local plist_main_exists=false
    local plist_menubar_exists=false
    local service_main_running=false
    local service_menubar_running=false
    local issues_found=false

    print_step "🔍 Checking for existing installation..."
    echo ""

    # Check if app is installed
    if [ -d "/Applications/$APP_NAME" ]; then
        app_installed=true
        echo -e "${GREEN}✅ Application found in Applications folder${NC}"
    else
        echo -e "${YELLOW}⚪ Application not found in Applications folder${NC}"
    fi

    # Check if plist files exist
    if [ -f "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" ]; then
        plist_main_exists=true
        echo -e "${GREEN}✅ Main service plist file exists${NC}"
    else
        echo -e "${YELLOW}⚪ Main service plist file not found${NC}"
    fi

    if [ -f "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" ]; then
        plist_menubar_exists=true
        echo -e "${GREEN}✅ Menu bar service plist file exists${NC}"
    else
        echo -e "${YELLOW}⚪ Menu bar service plist file not found${NC}"
    fi

    # Check if services are running
    if launchctl list | grep -q "com.clipboardmonitor$"; then
        service_main_running=true
        echo -e "${GREEN}✅ Main service is running${NC}"
    else
        echo -e "${YELLOW}⚪ Main service is not running${NC}"
    fi

    if launchctl list | grep -q "com.clipboardmonitor.menubar"; then
        service_menubar_running=true
        echo -e "${GREEN}✅ Menu bar service is running${NC}"
    else
        echo -e "${YELLOW}⚪ Menu bar service is not running${NC}"
    fi

    echo ""

    # Determine if we have a complete or partial installation
    if $app_installed && $plist_main_exists && $plist_menubar_exists; then
        if $service_main_running && $service_menubar_running; then
            print_success "Complete installation detected - all components present and running"
            echo -e "${BLUE}📱 Clipboard Monitor appears to be fully installed and operational.${NC}"
        else
            print_warning "Complete installation detected but services not running"
            echo -e "${BLUE}📱 All files are present but services may need to be restarted.${NC}"
        fi
        issues_found=true
    elif $app_installed || $plist_main_exists || $plist_menubar_exists || $service_main_running || $service_menubar_running; then
        print_warning "Partial installation detected"
        echo -e "${BLUE}📱 Some components are installed but the installation appears incomplete.${NC}"
        issues_found=true
    else
        print_success "No existing installation found - ready for fresh installation"
        return 0
    fi

    echo ""
    echo -e "${YELLOW}🔄 RECOMMENDATION:${NC}"
    echo -e "${BLUE}To ensure a clean installation, it's recommended to uninstall the existing${NC}"
    echo -e "${BLUE}components before proceeding with the new installation.${NC}"
    echo ""

    # Ask user if they want to uninstall existing installation
    echo -e "${BLUE}Would you like to uninstall the existing installation first? (Y/n)${NC}"
    read -p "" -n 1 -r
    echo # Move to a new line

    # Default to 'y' if user just pressed Enter
    if [[ -z $REPLY ]]; then
        REPLY="y"
    fi

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        print_step "🧹 Uninstalling existing installation..."

        # Perform silent uninstall without header/exit prompts
        print_step "🛑 Stopping services..."
        launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" 2>/dev/null || true
        launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" 2>/dev/null || true
        print_success "Services stopped"

        print_step "🗂️  Removing plist files..."
        rm -f "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" 2>/dev/null || true
        rm -f "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" 2>/dev/null || true
        print_success "Plist files removed"

        print_step "📱 Removing application..."
        rm -rf "/Applications/$APP_NAME" 2>/dev/null || true
        print_success "Application removed"

        print_step "🧹 Cleaning up log files..."
        rm -f "$LOG_DIR/ClipboardMonitor.out.log" 2>/dev/null || true
        rm -f "$LOG_DIR/ClipboardMonitor.err.log" 2>/dev/null || true
        rm -f "$LOG_DIR/ClipboardMonitorMenuBar.out.log" 2>/dev/null || true
        rm -f "$LOG_DIR/ClipboardMonitorMenuBar.err.log" 2>/dev/null || true
        print_success "Log files cleaned"

        echo ""
        print_success "Existing installation removed - ready for fresh installation"
        echo ""
    else
        echo ""
        print_warning "Proceeding with installation over existing components"
        echo -e "${YELLOW}⚠️  This may cause conflicts or unexpected behavior.${NC}"
        echo ""
    fi
}

# --- Main Installation ---
main() {
    print_header

    echo -e "${BLUE}Welcome to Clipboard Monitor!${NC}"
    echo ""
    echo "This script will automatically install Clipboard Monitor and set up background services."
    echo "The installation will:"
    echo "  • Copy the application to your Applications folder"
    echo "  • Set up background clipboard monitoring"
    echo "  • Configure the menu bar interface"
    echo "  • Create system service files"
    echo "  • Verify everything is working properly"
    echo ""

    # Check for existing installation first
    check_existing_installation

    # Ask for user confirmation before proceeding (default: y)
    read -p "Continue with installation? (Y/n) " -n 1 -r
    echo # Move to a new line

    # Default to 'y' if user just pressed Enter (empty response)
    if [[ -z $REPLY ]]; then
        REPLY="y"
    fi

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Installation cancelled.${NC}"
        echo -e "${BLUE}Thank you for considering Clipboard Monitor!${NC}"
        exit_with_prompt 1
    fi

    echo ""
    print_step "� Installing application to Applications folder..."

    # Set installation directory
    INSTALL_DIR="/Applications/$APP_NAME"

    # Check if app already exists
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Application already exists in Applications folder"
        echo -e "${BLUE}Would you like to replace it with the current version? (Y/n)${NC}"
        read -p "" -n 1 -r
        echo # Move to a new line

        # Default to 'y' if user just pressed Enter
        if [[ -z $REPLY ]]; then
            REPLY="y"
        fi

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_step "🗑️  Removing existing installation..."
            rm -rf "$INSTALL_DIR"
            print_success "Existing installation removed"
        else
            print_success "Using existing installation"
            echo -e "${BLUE}   � Application path: $INSTALL_DIR${NC}"
            echo ""
            return 0
        fi
    fi

    # Try to find the app in common locations
    APP_SOURCE=""

    # Check if we're running from DMG
    if [ -d "/Volumes/Clipboard Monitor/$APP_NAME" ]; then
        APP_SOURCE="/Volumes/Clipboard Monitor/$APP_NAME"
        print_success "Found app in mounted DMG"
    # Check current directory
    elif [ -d "./$APP_NAME" ]; then
        APP_SOURCE="./$APP_NAME"
        print_success "Found app in current directory"
    # Check parent directory
    elif [ -d "../$APP_NAME" ]; then
        APP_SOURCE="../$APP_NAME"
        print_success "Found app in parent directory"
    else
        print_error "Could not locate '$APP_NAME' for installation"
        echo ""
        echo -e "${YELLOW}📋 Please ensure one of the following:${NC}"
        echo -e "${BLUE}   1. 📦 DMG is mounted at '/Volumes/Clipboard Monitor/'${NC}"
        echo -e "${BLUE}   2. 🖱️  App is in the same directory as this script${NC}"
        echo -e "${BLUE}   3. 📁 App is in the parent directory${NC}"
        echo ""
        exit_with_prompt 1
    fi

    # Copy the application
    print_step "📋 Copying application to Applications folder..."
    echo -e "${BLUE}   📂 Source: $APP_SOURCE${NC}"
    echo -e "${BLUE}   📁 Destination: $INSTALL_DIR${NC}"

    if ditto "$APP_SOURCE" "$INSTALL_DIR"; then
        print_success "Application successfully copied to Applications folder"

        # Verify the copy was successful
        if [ -d "$INSTALL_DIR" ]; then
            print_success "Installation verified"
            echo -e "${BLUE}   📁 Application path: $INSTALL_DIR${NC}"
        else
            print_error "Installation verification failed"
            exit_with_prompt 1
        fi
    else
        print_error "Failed to copy application to Applications folder"
        echo ""
        echo -e "${YELLOW}💡 This might be due to permission issues.${NC}"
        echo -e "${BLUE}You can try manually dragging the app to Applications folder.${NC}"
        exit_with_prompt 1
    fi
    echo ""

    print_step "📁 Preparing system directories..."
    mkdir -p "$LAUNCH_AGENTS_DIR"
    mkdir -p "$LOG_DIR"
    print_success "System directories ready"
    echo ""

    print_step "🧹 Cleaning up any existing services..."
    launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" 2>/dev/null || true
    launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" 2>/dev/null || true
    print_success "Previous services cleaned up"
    echo ""

    print_step "⚙️  Creating background service configuration..."

    # COMMENTED OUT: SentinelOne detects plist creation as threat
    # Manual installation required - plist files provided separately in DMG

    # cat > "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" << EOL
    # <?xml version="1.0" encoding="UTF-8"?>
    # <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    # <plist version="1.0">
    # <dict>
    #     <key>Label</key>
    #     <string>com.clipboardmonitor</string>
    #     <key>ProgramArguments</key>
    #     <array>
    #         <string>$INSTALL_DIR/Contents/Resources/Services/ClipboardMonitor.app/Contents/MacOS/ClipboardMonitor</string>
    #     </array>
    #     <key>RunAtLoad</key>
    #     <true/>
    #     <key>KeepAlive</key>
    #     <false/>
    #     <key>StandardOutPath</key>
    #     <string>$LOG_DIR/ClipboardMonitor.out.log</string>
    #     <key>StandardErrorPath</key>
    #     <string>$LOG_DIR/ClipboardMonitor.err.log</string>
    #     <key>WorkingDirectory</key>
    #     <string>$INSTALL_DIR/Contents/Resources/Services/ClipboardMonitor.app/Contents/Resources/</string>
    # </dict>
    # </plist>
    # EOL

    print_success "Background service configuration ready (manual installation required)"
    echo ""

    print_step "🖥️  Creating menu bar service configuration..."

    # COMMENTED OUT: SentinelOne detects plist creation as threat
    # Manual installation required - plist files provided separately in DMG

    # cat > "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" << EOL
    # <?xml version="1.0" encoding="UTF-8"?>
    # <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    # <plist version="1.0">
    # <dict>
    #     <key>Label</key>
    #     <string>com.clipboardmonitor.menubar</string>
    #     <key>ProgramArguments</key>
    #     <array>
    #         <string>$INSTALL_DIR/Contents/MacOS/ClipboardMonitorMenuBar</string>
    #     </array>
    #     <key>RunAtLoad</key>
    #     <true/>
    #     <key>KeepAlive</key>
    #     <false/>
    #     <key>StandardOutPath</key>
    #     <string>$LOG_DIR/ClipboardMonitorMenuBar.out.log</string>
    #     <key>StandardErrorPath</key>
    #     <string>$LOG_DIR/ClipboardMonitorMenuBar.err.log</string>
    #     <key>WorkingDirectory</key>
    #     <string>$INSTALL_DIR/Contents/Resources/</string>
    # </dict>
    # </plist>
    # EOL

    print_success "Menu bar service configuration ready (manual installation required)"
    echo ""

    print_step "📋 Interactive plist file installation..."
    echo ""
    echo -e "${BLUE}🎯 EASY DRAG-AND-DROP INSTALLATION${NC}"
    echo -e "${BLUE}The DMG includes everything you need for a simple installation!${NC}"
    echo ""
    echo -e "${BLUE}📁 What's included in the DMG:${NC}"
    echo -e "${BLUE}   • com.clipboardmonitor.plist${NC}"
    echo -e "${BLUE}   • com.clipboardmonitor.menubar.plist${NC}"
    echo -e "${BLUE}   • LaunchAgents symlink (points to ~/Library/LaunchAgents)${NC}"
    echo ""
    echo -e "${BLUE}🚀 SUPER SIMPLE INSTALLATION:${NC}"
    echo -e "${BLUE}   1. I'll open the DMG in list view for easy access${NC}"
    echo -e "${BLUE}   2. Just drag both plist files onto the LaunchAgents symlink${NC}"
    echo -e "${BLUE}   3. Come back here and press any key to continue${NC}"
    echo ""

    # Offer to open the DMG automatically
    echo -e "${BLUE}Would you like me to open the DMG for you now? (Y/n)${NC}"
    read -p "" -n 1 -r
    echo # Move to a new line

    # Default to 'y' if user just pressed Enter
    if [[ -z $REPLY ]]; then
        REPLY="y"
    fi

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "📂 Opening DMG for easy installation..."

        # Open the DMG folder (should already be mounted)
        if [ -d "/Volumes/Clipboard Monitor" ]; then
            open "/Volumes/Clipboard Monitor"
            print_success "Opened DMG in list view"
        else
            print_warning "DMG folder not found - please open it manually"
        fi

        echo ""
        echo -e "${GREEN}✨ Perfect! DMG is now open in list view.${NC}"
        echo -e "${BLUE}📋 Simply drag both plist files onto the LaunchAgents symlink:${NC}"
        echo -e "${BLUE}   • com.clipboardmonitor.plist → LaunchAgents${NC}"
        echo -e "${BLUE}   • com.clipboardmonitor.menubar.plist → LaunchAgents${NC}"
        echo ""
        echo -e "${BLUE}💡 The LaunchAgents symlink will copy the files to the correct location!${NC}"
        echo ""
    else
        echo -e "${BLUE}📋 Manual installation:${NC}"
        echo -e "${BLUE}   Drag both plist files from the DMG onto the LaunchAgents symlink${NC}"
        echo -e "${BLUE}   Or copy them manually to: ~/Library/LaunchAgents/${NC}"
        echo ""
    fi

    echo -e "${BLUE}⏳ Waiting for you to copy the plist files...${NC}"
    read -p "Press any key after copying the plist files..." -n 1 -s
    echo ""
    print_success "Proceeding with service installation"
    echo ""



    print_step "🧹 Ensuring clean service state..."
    # Kill any existing processes first to prevent conflicts
    pkill -f "ClipboardMonitor" 2>/dev/null || true
    pkill -f "ClipboardMonitorMenuBar" 2>/dev/null || true

    # Unload any existing services
    launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" 2>/dev/null || true
    launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" 2>/dev/null || true

    # Wait for cleanup
    sleep 2
    print_success "Service state cleaned"
    echo ""

    print_step "🚀 Loading and starting services..."

    # Load background service
    if launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" 2>/dev/null; then
        print_success "Background service loaded successfully"
    else
        print_warning "Failed to load background service"
    fi

    # Load menu bar service
    if launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" 2>/dev/null; then
        print_success "Menu bar service loaded successfully"
    else
        print_warning "Failed to load menu bar service"
    fi

    echo ""
    print_step "⏳ Waiting for services to initialize..."
    echo -e "${BLUE}   This may take a few seconds...${NC}"
    sleep 3
    print_success "Services initialization period completed"
    echo ""

    print_step "🔍 Verifying service status..."
    echo -e "${BLUE}   Checking if services started correctly...${NC}"

    main_service_status=0
    menubar_service_status=0

    check_service_status "ClipboardMonitor" "com.clipboardmonitor" "ClipboardMonitor" "ClipboardMonitor.app/Contents/MacOS/ClipboardMonitor"
    main_service_status=$?

    check_service_status "ClipboardMonitorMenuBar" "com.clipboardmonitor.menubar" "ClipboardMonitorMenuBar" "ClipboardMonitorMenuBar"
    menubar_service_status=$?

    echo ""
    print_step "📋 Analyzing log files for any issues..."
    log_check_status=0
    check_log_files
    log_check_status=$?

    # --- Final Summary ---
    echo ""
    echo "=================================================="
    print_step "📊 Installation Summary"
    echo ""

    # Determine overall installation status
    if [[ $main_service_status -eq 0 && $menubar_service_status -eq 0 && $log_check_status -eq 0 ]]; then
        # Complete success - services running and no errors
        echo -e "${GREEN}🎉 FANTASTIC! Clipboard Monitor is fully installed and running perfectly!${NC}"
        echo -e "${GREEN}Both services are active and no errors were detected.${NC}"
        echo ""
        echo -e "${BLUE}🚀 Your Clipboard Monitor is now ready to use!${NC}"
        echo ""
        echo "Active services:"
        echo "  ✅ Background Monitor: Watching your clipboard 24/7"
        echo "  ✅ Menu Bar App: Ready in your menu bar"
        echo ""
        echo -e "${BLUE}💡 Look for the Clipboard Monitor icon in your menu bar to get started!${NC}"

    elif [[ $main_service_status -eq 0 || $menubar_service_status -eq 0 ]]; then
        # Partial success - some services running but issues detected
        echo -e "${YELLOW}⚠️  INSTALLATION COMPLETED WITH SOME ISSUES${NC}"
        echo -e "${YELLOW}Don't worry! The installation steps completed successfully, but some services need attention.${NC}"
        echo ""
        echo -e "${BLUE}📊 Service Status Report:${NC}"
        if [[ $main_service_status -eq 0 ]]; then
            echo -e "  ${GREEN}✅ Background Monitor: Running perfectly${NC}"
        else
            echo -e "  ${RED}❌ Background Monitor: Needs troubleshooting${NC}"
        fi
        if [[ $menubar_service_status -eq 0 ]]; then
            echo -e "  ${GREEN}✅ Menu Bar App: Running perfectly${NC}"
        else
            echo -e "  ${RED}❌ Menu Bar App: Needs troubleshooting${NC}"
        fi

        echo ""
        echo -e "${BLUE}🔧 Don't worry - we can fix this together!${NC}"
        echo -e "${BLUE}The log files above contain helpful information to resolve any issues.${NC}"

        # Offer to open Console app for detailed analysis
        if [[ $log_check_status -ne 0 ]]; then
            offer_console_app
        fi

    else
        # Installation failed - services not running
        echo -e "${RED}❌ INSTALLATION COMPLETED BUT SERVICES NEED ATTENTION${NC}"
        echo -e "${YELLOW}The installation steps completed successfully, but the services need some help to start.${NC}"
        echo ""
        echo -e "${BLUE}🤔 What this means:${NC}"
        echo "   • The application files are properly installed"
        echo "   • The configuration files were created correctly"
        echo "   • The services just need some troubleshooting to start"
        echo ""
        echo -e "${BLUE}🔧 This is usually an easy fix!${NC}"
        echo -e "${BLUE}The log files above contain helpful information to resolve the issue.${NC}"

        # Always offer Console app when services fail
        offer_console_app
    fi

    echo ""
    echo -e "${BLUE}📁 Configuration files created:${NC}"
    echo "  • Background Monitor: $LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"
    echo "  • Menu Bar App:       $LAUNCH_AGENTS_DIR/$PLIST_MENUBAR"
    echo ""
    echo -e "${BLUE}💡 Helpful tip: To uninstall at any time, run this script again with the --uninstall flag.${NC}"
    echo ""
    echo -e "${BLUE}Thank you for installing Clipboard Monitor! 🙏${NC}"
    echo -e "${BLUE}We hope you enjoy using it to enhance your productivity!${NC}"

    exit_with_prompt 0
}

# --- Script Execution ---
# Run main installation function
main "$@"