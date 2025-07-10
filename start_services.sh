#!/bin/bash
# Start Clipboard Monitor Services

# Source the shared configuration
source "$(dirname "$0")/_config.sh"

echo -e "${YELLOW}${ICON_START} Starting all Clipboard Monitor services...${NC}"
echo "--------------------------------------------------"

# Start the main Clipboard Monitor service by loading it into launchd
echo "1. Loading Main Service ($PLIST_BACKGROUND)..."
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND" &> /dev/null
echo -e "   ${GREEN}${ICON_SUCCESS} Main service loaded.${NC}"

# Start the Menu Bar app by loading it into launchd
echo "2. Loading Menu Bar App ($PLIST_MENUBAR)..."
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR" &> /dev/null
echo -e "   ${GREEN}${ICON_SUCCESS} Menu Bar app loaded.${NC}"

echo "--------------------------------------------------"
echo -e "${GREEN}${ICON_SUCCESS} All services have been started.${NC}"
echo -e "${YELLOW}You should see the 📋 icon in your menu bar shortly.${NC}"