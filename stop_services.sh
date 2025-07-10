#!/bin/bash
# Stop Clipboard Monitor Services
#
# This script stops both the Clipboard Monitor service and the Menu Bar app.

# Source the shared configuration
source "$(dirname "$0")/_config.sh"

echo -e "${YELLOW}${ICON_STOP} Stopping all Clipboard Monitor services...${NC}"
echo "--------------------------------------------------"

# Stop the main Clipboard Monitor service by unloading it from launchd
echo "1. Unloading Main Service ($PLIST_BACKGROUND)..."
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" &> /dev/null
echo -e "   ${GREEN}${ICON_SUCCESS} Main service unloaded (if it was running).${NC}"

# Stop the Menu Bar app by unloading it from launchd
echo "2. Unloading Menu Bar App ($PLIST_MENUBAR)..."
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" &> /dev/null
echo -e "   ${GREEN}${ICON_SUCCESS} Menu Bar app unloaded (if it was running).${NC}"

echo "--------------------------------------------------"
echo -e "${GREEN}${ICON_SUCCESS} All services have been stopped.${NC}"