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

# ANSI color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Restarting Clipboard Monitor services...${NC}"

# Restart the main Clipboard Monitor service
echo -e "${GREEN}Restarting main Clipboard Monitor service...${NC}"
launchctl unload ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully unloaded main service${NC}"
else
    echo -e "${RED}Failed to unload main service${NC}"
fi

sleep 1

launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully loaded main service${NC}"
else
    echo -e "${RED}Failed to load main service${NC}"
fi

# Restart the Menu Bar app
echo -e "${GREEN}Restarting Menu Bar app...${NC}"
launchctl unload ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.menubar.plist
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully unloaded Menu Bar app${NC}"
else
    echo -e "${RED}Failed to unload Menu Bar app${NC}"
fi

sleep 1

launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.menubar.plist
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully loaded Menu Bar app${NC}"
else
    echo -e "${RED}Failed to load Menu Bar app${NC}"
fi

echo -e "${YELLOW}Restart complete!${NC}"
echo -e "${GREEN}You should now see the Clipboard Monitor icon in your menu bar.${NC}"