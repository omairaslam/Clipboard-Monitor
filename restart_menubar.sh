#!/bin/bash
# Restart only the Menu Bar App service.

# Source the shared configuration
source "$(dirname "$0")/_config.sh"

echo -e "${YELLOW}${ICON_RESTART} Restarting Menu Bar App...${NC}"
echo "--------------------------------------------------"

launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" &> /dev/null
sleep 1
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" &> /dev/null

if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}${ICON_SUCCESS} Menu Bar app restarted successfully.${NC}"
else
    echo -e "   ${RED}${ICON_ERROR} Failed to restart Menu Bar app.${NC}"
fi
echo "--------------------------------------------------"