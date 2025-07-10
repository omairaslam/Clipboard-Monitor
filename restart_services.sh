#!/bin/bash
# Restart Clipboard Monitor Services
#
# This script restarts both the Clipboard Monitor service and the Menu Bar app.
#
# Usage:
#   1. Make this script executable: chmod +x restart_services.sh
#   2. Run the script: ./restart_services.sh
#
# You can also run it with bash: bash restart_services.sh

# Source the shared configuration
source "$(dirname "$0")/_config.sh"

echo -e "${YELLOW}${ICON_RESTART} Restarting all Clipboard Monitor services...${NC}"
echo "--------------------------------------------------"

# Restart the main Clipboard Monitor service
echo "1. Restarting Main Service ($PLIST_BACKGROUND)..."
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" &> /dev/null
sleep 1
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" &> /dev/null
if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}${ICON_SUCCESS} Main service restarted successfully.${NC}"
else
    echo -e "   ${RED}${ICON_ERROR} Failed to restart main service.${NC}"
fi

# Restart the Menu Bar app
echo "2. Restarting Menu Bar App ($PLIST_MENUBAR)..."
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" &> /dev/null
sleep 1
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" &> /dev/null
if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}${ICON_SUCCESS} Menu Bar app restarted successfully.${NC}"
else
    echo -e "   ${RED}${ICON_ERROR} Failed to restart Menu Bar app.${NC}"
fi

echo "--------------------------------------------------"
echo -e "${GREEN}${ICON_SUCCESS} Restart complete! You should see the 📋 icon in your menu bar shortly.${NC}"