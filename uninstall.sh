#!/bin/bash

# Clipboard Monitor - Complete Uninstall Script
# This script completely removes all traces of Clipboard Monitor from the system
#
# Updated to detect compiled executables (ClipboardMonitor, ClipboardMonitorMenuBar)
# instead of Python files (main.py, menu_bar_app.py) for current app structure
#
# Note: Removed 'set -e' to handle errors gracefully with user prompts

# --- Configuration & Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Define application and system paths
APP_NAME="Clipboard Monitor.app"
APPLICATIONS_DIR="/Applications"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$HOME/Library/Logs"
APP_SUPPORT_DIR="$HOME/Library/Application Support/ClipboardMonitor"

# LaunchAgent plist files
PLIST_BACKGROUND="com.clipboardmonitor.plist"
PLIST_MENUBAR="com.clipboardmonitor.menubar.plist"

# Service labels for launchctl
SERVICE_BACKGROUND="com.clipboardmonitor"
SERVICE_MENUBAR="com.clipboardmonitor.menubar"

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
    local service_display_name="$1"
    local service_label="$2"
    local process_name="$3"
    local log_prefix="$4"

    echo -e "${BLUE}📊 Checking $service_display_name status...${NC}"

    # Check if service is loaded in launchctl
    if launchctl list | grep -q "$service_label"; then
        echo -e "${GREEN}✅ $service_display_name is loaded${NC}"

        # Check if process is running using multiple detection methods
        local process_running=false

        # Method 1: Check by exact process name
        if pgrep -x "$process_name" > /dev/null 2>&1; then
            process_running=true
        # Method 2: Check by partial name match
        elif pgrep "$process_name" > /dev/null 2>&1; then
            process_running=true
        # Method 3: Check for clipboard-related processes (fallback)
        elif pgrep -f "ClipboardMonitor" > /dev/null 2>&1; then
            process_running=true
        fi

        if $process_running; then
            echo -e "${GREEN}✅ $service_display_name is running${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  $service_display_name is loaded but not running${NC}"
            if [[ -n "$log_prefix" ]]; then
                show_service_logs "$log_prefix" "$service_display_name"
            fi
            return 1
        fi
    else
        echo -e "${RED}❌ $service_display_name is not loaded${NC}"
        return 1
    fi
}

# Function to show recent log entries for failed services
show_service_logs() {
    local log_prefix="$1"
    local service_name="$2"
    local log_dir="$HOME/Library/Logs"

    echo -e "${BLUE}📋 Recent logs for $service_name:${NC}"

    # Show error log if it exists and has content
    if [[ -f "$log_dir/${log_prefix}.err.log" ]] && [[ -s "$log_dir/${log_prefix}.err.log" ]]; then
        echo -e "${RED}❌ Error log (last 5 lines):${NC}"
        tail -5 "$log_dir/${log_prefix}.err.log" | sed 's/^/   /'
    fi

    # Show output log if it exists and has content
    if [[ -f "$log_dir/${log_prefix}.out.log" ]] && [[ -s "$log_dir/${log_prefix}.out.log" ]]; then
        echo -e "${BLUE}📄 Output log (last 5 lines):${NC}"
        tail -5 "$log_dir/${log_prefix}.out.log" | sed 's/^/   /'
    fi

    # If no logs exist or are empty
    if [[ ! -f "$log_dir/${log_prefix}.err.log" ]] && [[ ! -f "$log_dir/${log_prefix}.out.log" ]]; then
        echo -e "${YELLOW}⚠️  No log files found - service may not have attempted to start${NC}"
    elif [[ ! -s "$log_dir/${log_prefix}.err.log" ]] && [[ ! -s "$log_dir/${log_prefix}.out.log" ]]; then
        echo -e "${YELLOW}⚠️  Log files exist but are empty - service may have started and stopped immediately${NC}"
    fi
    echo ""
}

# Log files to remove
LOG_FILES=(
    "ClipboardMonitor.out.log"
    "ClipboardMonitor.err.log"
    "ClipboardMonitorMenuBar.out.log"
    "ClipboardMonitorMenuBar.err.log"
)

# Application Support files and directories
APP_SUPPORT_FILES=(
    "clipboard_history.json"
    "clipboard_history.corrupt.bak"
    "clipboard_monitor.out.log"
    "clipboard_monitor.err.log"
    "memory_data.json"
    "leak_analysis.json"
    "menubar_profile.json"
    "advanced_profile.json"
    "longterm_monitoring.json"
    "config.json"
    "status.txt"
    "pause_flag"
)

# --- Functions ---
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}    Clipboard Monitor - Complete Uninstaller${NC}"
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

# Function to stop and unload services
stop_services() {
    print_step "🛑 Stopping Clipboard Monitor services..."

    # Stop background service
    if launchctl list | grep -q "$SERVICE_BACKGROUND"; then
        launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" 2>/dev/null || true
        print_success "Background service stopped"
    else
        print_warning "Background service was not running"
    fi

    # Stop menu bar service
    if launchctl list | grep -q "$SERVICE_MENUBAR"; then
        launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" 2>/dev/null || true
        print_success "Menu bar service stopped"
    else
        print_warning "Menu bar service was not running"
    fi

    # Force kill any remaining processes using updated process names
    # Kill compiled executables
    pkill -x "ClipboardMonitor" 2>/dev/null || true
    pkill -x "ClipboardMonitorMenuBar" 2>/dev/null || true

    # Kill any clipboard-related processes (broader match)
    pkill -f "ClipboardMonitor" 2>/dev/null || true
    pkill -f "Clipboard Monitor" 2>/dev/null || true

    # Legacy process names (for backward compatibility)
    pkill -f "main.py" 2>/dev/null || true
    pkill -f "menu_bar_app.py" 2>/dev/null || true

    # Give processes time to terminate
    sleep 2

    print_success "All services stopped"
}

# Function to remove LaunchAgent plist files
remove_launch_agents() {
    print_step "🗂️  Removing LaunchAgent configuration files..."
    
    removed_count=0
    
    if [ -f "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" ]; then
        rm -f "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"
        print_success "Removed: $PLIST_BACKGROUND"
        ((removed_count++))
    fi
    
    if [ -f "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" ]; then
        rm -f "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR"
        print_success "Removed: $PLIST_MENUBAR"
        ((removed_count++))
    fi
    
    if [ $removed_count -eq 0 ]; then
        print_warning "No LaunchAgent files found"
    else
        print_success "Removed $removed_count LaunchAgent file(s)"
    fi
}

# Function to remove application
remove_application() {
    print_step "🗑️  Removing application..."
    
    if [ -d "$APPLICATIONS_DIR/$APP_NAME" ]; then
        rm -rf "$APPLICATIONS_DIR/$APP_NAME"
        print_success "Removed: $APP_NAME from Applications"
    else
        print_warning "Application not found in Applications folder"
    fi
}

# Function to remove log files
remove_log_files() {
    print_step "📝 Removing log files..."
    
    removed_count=0
    
    for log_file in "${LOG_FILES[@]}"; do
        full_path="$LOG_DIR/$log_file"
        if [ -f "$full_path" ]; then
            rm -f "$full_path"
            print_success "Removed: $log_file"
            ((removed_count++))
        fi
    done
    
    # Remove log directory if it exists and is empty
    if [ -d "$LOG_DIR/ClipboardMonitor" ]; then
        rmdir "$LOG_DIR/ClipboardMonitor" 2>/dev/null || true
        if [ ! -d "$LOG_DIR/ClipboardMonitor" ]; then
            print_success "Removed: ClipboardMonitor log directory"
            ((removed_count++))
        fi
    fi
    
    if [ $removed_count -eq 0 ]; then
        print_warning "No log files found"
    else
        print_success "Removed $removed_count log file(s)"
    fi
}

# Function to remove application support files
remove_app_support() {
    print_step "📁 Removing application data and configuration..."
    
    if [ -d "$APP_SUPPORT_DIR" ]; then
        removed_count=0
        
        # Remove specific files
        for app_file in "${APP_SUPPORT_FILES[@]}"; do
            full_path="$APP_SUPPORT_DIR/$app_file"
            if [ -f "$full_path" ]; then
                rm -f "$full_path"
                print_success "Removed: $app_file"
                ((removed_count++))
            fi
        done
        
        # Remove any remaining files and the directory
        if [ -d "$APP_SUPPORT_DIR" ]; then
            rm -rf "$APP_SUPPORT_DIR"
            print_success "Removed: Application Support directory"
            ((removed_count++))
        fi
        
        if [ $removed_count -eq 0 ]; then
            print_warning "No application data found"
        else
            print_success "Removed $removed_count application data item(s)"
        fi
    else
        print_warning "Application Support directory not found"
    fi
}

# Function to verify complete removal
verify_removal() {
    print_step "🔍 Verifying complete removal..."

    issues_found=0

    # Check for remaining processes using updated detection
    local remaining_processes=false

    # Check for compiled executables
    if pgrep -x "ClipboardMonitor" >/dev/null 2>&1 || pgrep -x "ClipboardMonitorMenuBar" >/dev/null 2>&1; then
        remaining_processes=true
    fi

    # Check for any clipboard-related processes
    if pgrep -f "ClipboardMonitor\|Clipboard Monitor" >/dev/null 2>&1; then
        remaining_processes=true
    fi

    # Check for legacy Python processes (backward compatibility)
    if pgrep -f "main.py\|menu_bar_app.py" >/dev/null 2>&1; then
        remaining_processes=true
    fi

    if $remaining_processes; then
        print_error "Some processes are still running"
        echo -e "${YELLOW}   Running processes:${NC}"
        pgrep -fl "ClipboardMonitor\|Clipboard Monitor\|main.py\|menu_bar_app.py" 2>/dev/null | sed 's/^/   /' || true
        ((issues_found++))
    fi
    
    # Check for remaining LaunchAgent files
    if [ -f "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" ] || [ -f "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" ]; then
        print_error "Some LaunchAgent files still exist"
        ((issues_found++))
    fi
    
    # Check for remaining application
    if [ -d "$APPLICATIONS_DIR/$APP_NAME" ]; then
        print_error "Application still exists in Applications folder"
        ((issues_found++))
    fi
    
    # Check for remaining application support directory
    if [ -d "$APP_SUPPORT_DIR" ]; then
        print_error "Application Support directory still exists"
        ((issues_found++))
    fi
    
    if [ $issues_found -eq 0 ]; then
        print_success "Verification complete - all components removed successfully"
        return 0
    else
        print_error "Verification failed - $issues_found issue(s) found"
        return 1
    fi
}

# --- Main Execution ---
main() {
    print_header

    # Check current service status before uninstalling
    echo -e "${BLUE}🔍 Checking current service status...${NC}"
    echo ""
    check_service_status "Background Service" "$SERVICE_BACKGROUND" "ClipboardMonitor" "ClipboardMonitor"
    check_service_status "Menu Bar Service" "$SERVICE_MENUBAR" "ClipboardMonitorMenuBar" "ClipboardMonitorMenuBar"
    echo ""

    # Confirm uninstallation
    echo -e "${YELLOW}This will completely remove Clipboard Monitor and all its data.${NC}"
    echo -e "${YELLOW}This action cannot be undone.${NC}"
    echo ""
    read -p "Are you sure you want to continue? (Y/n): " -n 1 -r
    echo ""

    # Default to 'y' if user just pressed Enter (empty response)
    if [[ -z $REPLY ]]; then
        REPLY="y"
    fi

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Uninstallation cancelled.${NC}"
        exit_with_prompt 0
    fi
    
    echo ""
    print_step "🚀 Starting complete uninstallation..."
    echo ""
    
    # Execute uninstallation steps
    stop_services
    echo ""
    
    remove_launch_agents
    echo ""
    
    remove_application
    echo ""
    
    remove_log_files
    echo ""
    
    remove_app_support
    echo ""
    
    # Verify removal
    if verify_removal; then
        echo ""
        echo -e "${GREEN}🎉 Clipboard Monitor has been completely uninstalled!${NC}"
        echo ""
        echo -e "${BLUE}Thank you for using Clipboard Monitor.${NC}"
        exit_with_prompt 0
    else
        echo ""
        echo -e "${RED}⚠️  Uninstallation completed with some issues.${NC}"
        echo -e "${YELLOW}You may need to manually remove remaining components.${NC}"
        exit_with_prompt 1
    fi
}

# Run main function
main "$@"
