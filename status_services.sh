#!/bin/bash
# Check Status of Clipboard Monitor Services

# Source the shared configuration
source "$(dirname "$0")/_config.sh"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}    Clipboard Monitor - Service Status${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${YELLOW}${ICON_STATUS} Checking Clipboard Monitor service status...${NC}"
echo "--------------------------------------------------"

# Function to check a single service
check_service() {
    local label=$1
    local name=$2
    local output
    local pid

    # Grep for the service in the launchctl list
    # We use grep -E with a '$' anchor to ensure an exact match on the label
    # and prevent "com.clipboardmonitor" from also matching "com.clipboardmonitor.menubar".
    output=$(launchctl list | grep -E "${label}$")
    
    if [ -n "$output" ]; then
        # Service is loaded
        pid=$(echo "$output" | awk '{print $1}')
        if [[ "$pid" =~ ^[0-9]+$ ]]; then
            # Service is running with a PID. Check for pause flag, only for the main service.
            if [ -f "$PAUSE_FLAG_PATH" ] && [ "$label" == "${PLIST_BACKGROUND%.plist}" ]; then
                 echo -e "  ${ICON_PAUSED} ${YELLOW}Paused:${NC}\t $name (PID: $pid)"
            else
                 echo -e "  ${ICON_RUNNING} ${GREEN}Running:${NC}\t $name (PID: $pid)"
            fi
        else
            # Service is loaded but not running (PID is '-')
            echo -e "  ${ICON_STOPPED} ${RED}Stopped:${NC}\t $name (Loaded but not running)"
        fi
    else
        # Service is not loaded
        echo -e "  ${ICON_NOT_LOADED} ${RED}Not Loaded:${NC}\t $name"
    fi
}

# Check Main Service and Menu Bar App
main_service_running=false
menubar_service_running=false

# Check main service
output=$(launchctl list | grep -E "${PLIST_BACKGROUND%.plist}$")
if [ -n "$output" ]; then
    pid=$(echo "$output" | awk '{print $1}')
    if [[ "$pid" =~ ^[0-9]+$ ]]; then
        main_service_running=true
    fi
fi

# Check menu bar service
output=$(launchctl list | grep -E "${PLIST_MENUBAR%.plist}$")
if [ -n "$output" ]; then
    pid=$(echo "$output" | awk '{print $1}')
    if [[ "$pid" =~ ^[0-9]+$ ]]; then
        menubar_service_running=true
    fi
fi

check_service "${PLIST_BACKGROUND%.plist}" "Main Service"
check_service "${PLIST_MENUBAR%.plist}" "Menu Bar App"

echo "--------------------------------------------------"

# If services are not running, offer to show logs and open Console
if [[ "$main_service_running" == "false" || "$menubar_service_running" == "false" ]]; then
    echo ""
    echo -e "${YELLOW}⚠️  Some services are not running. Checking recent logs...${NC}"

    log_dir="$HOME/Library/Logs"
    has_errors=false

    # Check for errors in main service logs
    if [[ "$main_service_running" == "false" ]]; then
        echo ""
        echo -e "${BLUE}📋 Main Service logs:${NC}"

        if [[ -f "$log_dir/ClipboardMonitor.err.log" ]] && [[ -s "$log_dir/ClipboardMonitor.err.log" ]]; then
            echo -e "${RED}❌ Error log (last 10 lines):${NC}"
            tail -10 "$log_dir/ClipboardMonitor.err.log" | sed 's/^/   /'
            has_errors=true
        fi

        if [[ -f "$log_dir/ClipboardMonitor.out.log" ]] && [[ -s "$log_dir/ClipboardMonitor.out.log" ]]; then
            if grep -qi "error\|exception\|traceback\|failed\|cannot\|unable" "$log_dir/ClipboardMonitor.out.log"; then
                echo -e "${YELLOW}⚠️  Issues in output log (last 10 lines):${NC}"
                tail -10 "$log_dir/ClipboardMonitor.out.log" | sed 's/^/   /'
                has_errors=true
            fi
        fi
    fi

    # Check for errors in menu bar service logs
    if [[ "$menubar_service_running" == "false" ]]; then
        echo ""
        echo -e "${BLUE}📋 Menu Bar Service logs:${NC}"

        if [[ -f "$log_dir/ClipboardMonitorMenuBar.err.log" ]] && [[ -s "$log_dir/ClipboardMonitorMenuBar.err.log" ]]; then
            echo -e "${RED}❌ Error log (last 10 lines):${NC}"
            tail -10 "$log_dir/ClipboardMonitorMenuBar.err.log" | sed 's/^/   /'
            has_errors=true
        fi

        if [[ -f "$log_dir/ClipboardMonitorMenuBar.out.log" ]] && [[ -s "$log_dir/ClipboardMonitorMenuBar.out.log" ]]; then
            if grep -qi "error\|exception\|traceback\|failed\|cannot\|unable" "$log_dir/ClipboardMonitorMenuBar.out.log"; then
                echo -e "${YELLOW}⚠️  Issues in output log (last 10 lines):${NC}"
                tail -10 "$log_dir/ClipboardMonitorMenuBar.out.log" | sed 's/^/   /'
                has_errors=true
            fi
        fi
    fi

    # Offer Console app if there are errors
    if [[ "$has_errors" == "true" ]]; then
        echo ""
        echo -e "${BLUE}� Troubleshooting Assistant${NC}"
        echo -e "${BLUE}Would you like me to open the log files with Console app for detailed analysis? (y/N)${NC}"
        echo -e "${BLUE}This can help identify exactly what's causing the issues.${NC}"
        read -p "Choice: " -n 1 -r
        echo # Move to a new line

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            opened_count=0
            for log_file in "ClipboardMonitor.err.log" "ClipboardMonitor.out.log" "ClipboardMonitorMenuBar.err.log" "ClipboardMonitorMenuBar.out.log"; do
                if [[ -f "$log_dir/$log_file" ]]; then
                    open -a Console "$log_dir/$log_file"
                    ((opened_count++))
                fi
            done
            echo -e "${GREEN}✅ Opened $opened_count log files in Console for your analysis${NC}"
            echo -e "${BLUE}💡 Look for error messages or unusual patterns in the logs${NC}"
        else
            echo -e "${BLUE}ℹ️  No problem! You can always run this script again to check status${NC}"
        fi
    fi
fi

echo ""
echo -e "${BLUE}💡 Tip: Run './install.sh --uninstall' to remove services if needed${NC}"