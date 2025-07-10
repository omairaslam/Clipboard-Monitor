#!/bin/bash
# Restart only the main Clipboard Monitor service.

# Source the shared configuration
source "$(dirname "$0")/_config.sh"

echo -e "${YELLOW}${ICON_RESTART} Restarting Main Service...${NC}"
echo "--------------------------------------------------"

launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" &> /dev/null
sleep 1
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" &> /dev/null

if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}${ICON_SUCCESS} Main service restarted successfully.${NC}"
else
    echo -e "   ${RED}${ICON_ERROR} Failed to restart main service.${NC}"
fi
echo "--------------------------------------------------"