#!/bin/bash

# Fix Python Framework Paths in py2app Bundle
# This script fixes the dyld linking issue where the python binary
# looks for Python3 in the wrong location

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

APP_NAME="Clipboard Monitor.app"
APP_PATH="dist/$APP_NAME"
PYTHON_BINARY="$APP_PATH/Contents/MacOS/python"
MAIN_BINARY="$APP_PATH/Contents/MacOS/Clipboard Monitor"
FRAMEWORK_PATH="@executable_path/../Frameworks/Python3.framework/Versions/3.9/Python3"

echo -e "${BLUE}🔧 Fixing Python framework paths in app bundle...${NC}"

# Check if app bundle exists
if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}❌ App bundle not found: $APP_PATH${NC}"
    exit 1
fi

# Check if python binary exists
if [ ! -f "$PYTHON_BINARY" ]; then
    echo -e "${RED}❌ Python binary not found: $PYTHON_BINARY${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Current python binary dependencies:${NC}"
otool -L "$PYTHON_BINARY"

echo -e "${YELLOW}🔄 Fixing python binary framework path...${NC}"

# Fix the python binary to point to the correct framework path
install_name_tool -change "@executable_path/../../../../Python3" "$FRAMEWORK_PATH" "$PYTHON_BINARY"

echo -e "${GREEN}✅ Fixed python binary framework path${NC}"

# Also fix the main binary if it has the same issue
if [ -f "$MAIN_BINARY" ]; then
    echo -e "${YELLOW}📋 Checking main binary dependencies:${NC}"
    if otool -L "$MAIN_BINARY" | grep -q "@executable_path/../../../../Python3"; then
        echo -e "${YELLOW}🔄 Fixing main binary framework path...${NC}"
        install_name_tool -change "@executable_path/../../../../Python3" "$FRAMEWORK_PATH" "$MAIN_BINARY"
        echo -e "${GREEN}✅ Fixed main binary framework path${NC}"
    else
        echo -e "${GREEN}✅ Main binary framework path is already correct${NC}"
    fi
fi

echo -e "${YELLOW}📋 Updated python binary dependencies:${NC}"
otool -L "$PYTHON_BINARY"

# Verify the framework exists at the expected location
FRAMEWORK_FILE="$APP_PATH/Contents/Frameworks/Python3.framework/Versions/3.9/Python3"
if [ -f "$FRAMEWORK_FILE" ]; then
    echo -e "${GREEN}✅ Python3 framework found at correct location${NC}"
else
    echo -e "${RED}❌ Python3 framework not found at: $FRAMEWORK_FILE${NC}"
    exit 1
fi

# Re-sign the binaries after modification
echo -e "${YELLOW}🔏 Re-signing modified binaries...${NC}"
codesign --force --sign - "$PYTHON_BINARY"
if [ -f "$MAIN_BINARY" ]; then
    codesign --force --sign - "$MAIN_BINARY"
fi
echo -e "${GREEN}✅ Binaries re-signed successfully${NC}"

echo -e "${GREEN}🎉 Framework path fix completed successfully!${NC}"
