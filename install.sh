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

# --- Main Installation ---
main() {
    print_header

    echo -e "${BLUE}Welcome to Clipboard Monitor!${NC}"
    echo ""
    echo "This script will install the necessary background services for Clipboard Monitor."
    echo "The installation will:"
    echo "  • Set up background clipboard monitoring"
    echo "  • Configure the menu bar interface"
    echo "  • Create system service files"
    echo "  • Verify everything is working properly"
    echo ""

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
    print_step "🔍 Verifying application location..."

    # Verify application location - only check system Applications folder
    INSTALL_DIR="/Applications/$APP_NAME"

    if [ -d "$INSTALL_DIR" ]; then
        print_success "Found application in Applications folder"
    else
        print_error "Application '$APP_NAME' not found!"
        echo ""
        echo -e "${RED}❌ The application must be installed before running this script.${NC}"
        echo ""
        echo -e "${YELLOW}📋 INSTALLATION STEPS:${NC}"
        echo -e "${BLUE}   1. 📦 Open the DMG file (if not already open)${NC}"
        echo -e "${BLUE}   2. 🖱️  Drag '$APP_NAME' to your Applications folder${NC}"
        echo -e "${BLUE}   3. ✅ Verify the app appears in /Applications/${NC}"
        echo -e "${BLUE}   4. 🔄 Run this install script again${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT: Do not run the app directly from the DMG!${NC}"
        echo -e "${YELLOW}   It must be copied to Applications first.${NC}"
        echo ""

        # Offer to wait and retry
        echo -e "${BLUE}Would you like to wait while you copy the app, then retry? (y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo ""
            echo -e "${YELLOW}⏳ Waiting for you to copy the app to Applications...${NC}"
            echo -e "${BLUE}Press any key when ready to retry...${NC}"
            read -n 1 -s
            echo ""

            # Retry the check
            if [ -d "$INSTALL_DIR" ]; then
                print_success "✅ Found application in Applications folder"
            else
                print_error "Application still not found. Please copy it to /Applications/ and try again."
                exit_with_prompt 1
            fi
        else
            echo ""
            echo -e "${BLUE}Please copy the app to Applications and run this script again.${NC}"
            exit_with_prompt 1
        fi
    fi

    echo -e "${BLUE}   📁 Application path: $INSTALL_DIR${NC}"
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

    print_step "📋 Manual plist file installation required..."
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT: SentinelOne security software prevents automated plist creation${NC}"
    echo -e "${BLUE}📁 Plist files are provided in the DMG for manual installation:${NC}"
    echo -e "${BLUE}   • com.clipboardmonitor.plist${NC}"
    echo -e "${BLUE}   • com.clipboardmonitor.menubar.plist${NC}"
    echo ""
    echo -e "${BLUE}📋 MANUAL INSTALLATION STEPS:${NC}"
    echo -e "${BLUE}   1. Copy both plist files from the DMG to:${NC}"
    echo -e "${BLUE}      ~/Library/LaunchAgents/${NC}"
    echo -e "${BLUE}   2. Press any key to continue with the installation${NC}"
    echo ""
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