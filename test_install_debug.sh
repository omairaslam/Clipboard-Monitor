#!/bin/bash

# Debug version of install script to test exit behavior

# --- Configuration & Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_NAME="Clipboard Monitor.app"

# Function to handle script exit with user prompt
exit_with_prompt() {
    local exit_code=${1:-0}
    echo ""
    echo -e "${BLUE}Press any key to close this window...${NC}"
    read -n 1 -s
    exit $exit_code
}

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}    Clipboard Monitor - Installation (DEBUG)${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

main() {
    print_header
    
    echo -e "${BLUE}Welcome to Clipboard Monitor!${NC}"
    echo ""
    echo "This is a debug version to test exit behavior."
    echo ""
    
    # Test application location check
    SYSTEM_APP_PATH="/Applications/$APP_NAME"
    USER_APP_PATH="$HOME/Applications/$APP_NAME"
    INSTALL_DIR=""

    echo "Checking for app at: $SYSTEM_APP_PATH"
    echo "Checking for app at: $USER_APP_PATH"

    if [ -d "$SYSTEM_APP_PATH" ]; then
        INSTALL_DIR="$SYSTEM_APP_PATH"
        echo -e "${GREEN}✅ Found application in system Applications folder${NC}"
    elif [ -d "$USER_APP_PATH" ]; then
        INSTALL_DIR="$USER_APP_PATH"
        echo -e "${GREEN}✅ Found application in user Applications folder${NC}"
    else
        echo -e "${RED}❌ Could not find '$APP_NAME' in /Applications or ~/Applications${NC}"
        echo ""
        echo -e "${BLUE}Please ensure the application is installed before running this script.${NC}"
        echo -e "${BLUE}You can install it by dragging the app from the DMG to your Applications folder.${NC}"
        echo ""
        echo "DEBUG: About to call exit_with_prompt(1)"
        exit_with_prompt 1
    fi

    echo -e "${BLUE}📁 Application path: $INSTALL_DIR${NC}"
    echo ""
    echo -e "${GREEN}✅ Debug test completed successfully!${NC}"
    echo ""
    echo "DEBUG: About to call exit_with_prompt(0)"
    exit_with_prompt 0
}

# Check for the --uninstall flag
if [ "$1" == "--uninstall" ]; then
    echo "Uninstall mode - exiting with prompt"
    exit_with_prompt 0
fi

echo "DEBUG: Starting main function"
main "$@"
echo "DEBUG: This line should never be reached"
