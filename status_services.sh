#!/bin/bash
# Check Status of Clipboard Monitor Services

# Source the shared configuration
source "$(dirname "$0")/_config.sh"

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
    # and prevent "com.omairaslam.clipboardmonitor" from also matching "com.omairaslam.clipboardmonitor.menubar".
    output=$(launchctl list | grep -E "${label}$")
    
    if [ -n "$output" ]; then
        # Service is loaded
        pid=$(echo "$output" | awk '{print $1}')
        if [[ "$pid" =~ ^[0-9]+$ ]]; then
            # Service is running with a PID. Check for pause flag, only for the main service.
            if [ -f "$PAUSE_FLAG_PATH" ] && [ "$label" == "$PLIST_BACKGROUND_LABEL" ]; then
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
check_service "$PLIST_BACKGROUND_LABEL" "Main Service"
check_service "$PLIST_MENUBAR_LABEL" "Menu Bar App"

echo "--------------------------------------------------"