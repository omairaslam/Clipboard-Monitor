#!/bin/bash

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing dependencies for Clipboard Monitor...${NC}"

# Install required packages
echo -e "${YELLOW}Installing Python packages...${NC}"
python3 -m pip install --user pyperclip rich pyobjc-framework-Cocoa rumps

# Test imports
echo -e "${YELLOW}Testing imports...${NC}"
python3 -c "import pyperclip; print('✅ pyperclip')" || echo -e "${RED}❌ pyperclip import failed${NC}"
python3 -c "import rich; print('✅ rich')" || echo -e "${RED}❌ rich import failed${NC}"
python3 -c "import AppKit; print('✅ pyobjc-framework-Cocoa')" || echo -e "${RED}❌ pyobjc-framework-Cocoa import failed${NC}"
python3 -c "import rumps; print('✅ rumps')" || echo -e "${RED}❌ rumps import failed${NC}"

echo -e "${GREEN}Installation complete!${NC}"
echo -e "${YELLOW}To install the menu bar app, run:${NC}"
echo -e "cp com.omairaslam.clipboardmonitor.menubar.plist ~/Library/LaunchAgents/"
echo -e "launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.menubar.plist"
