#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration & Colors ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}--- Clipboard Monitor Developer Setup ---${NC}"

# --- Step 1: Verify Python ---
echo -e "\n${GREEN}1. Verifying Python 3 installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed or not in your PATH.${NC}"
    echo "Please install Python 3 to continue."
    exit 1
fi
python3 --version
echo -e "${GREEN}✅ Python 3 found.${NC}"

# --- Step 2: Install Python Dependencies ---
echo -e "\n${GREEN}2. Installing Python dependencies from requirements.txt...${NC}"
python3 -m pip install --user -r requirements.txt
echo -e "${GREEN}✅ Python dependencies installed.${NC}"

# --- Step 3: Set Execute Permissions for Management Scripts ---
echo -e "\n${GREEN}3. Setting execute permissions for all management scripts...${NC}"
chmod +x *.sh
echo "   - build.sh"
echo "   - dashboard.sh"
echo "   - clear_logs.sh"
echo "   - install.sh"
echo "   - install_dependencies.sh"
echo "   - restart_main.sh"
echo "   - restart_menubar.sh"
echo "   - restart_services.sh"
echo "   - start_services.sh"
echo "   - status_services.sh"
echo "   - stop_services.sh"
echo -e "${GREEN}✅ All scripts are now executable.${NC}"

echo -e "\n${GREEN}🎉 Developer setup complete! All scripts are ready to use.${NC}"
