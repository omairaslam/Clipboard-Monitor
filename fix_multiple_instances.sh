#!/bin/bash

# Fix Multiple ClipboardMonitor Instances
# This script removes old plist files with KeepAlive=true and cleans up the system

echo "🔧 Fixing Multiple ClipboardMonitor Instances"
echo "============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Kill all running ClipboardMonitor processes
print_status "Killing all ClipboardMonitor processes..."
pkill -f "ClipboardMonitor" 2>/dev/null || true
sleep 2
print_success "All ClipboardMonitor processes terminated"
echo ""

# Step 2: Unload all clipboard-related LaunchAgents
print_status "Unloading all clipboard-related LaunchAgents..."
find "$HOME/Library/LaunchAgents" -name "*clipboard*" -o -name "*monitor*" | while read plist_file; do
    if [ -f "$plist_file" ]; then
        echo "Unloading: $plist_file"
        launchctl unload "$plist_file" 2>/dev/null || true
    fi
done
print_success "All LaunchAgents unloaded"
echo ""

# Step 3: Remove old plist files with KeepAlive=true
print_status "Removing old plist files with KeepAlive=true..."
OLD_PLIST_DIR="$HOME/Library/LaunchAgents/Omair Temp"
if [ -d "$OLD_PLIST_DIR" ]; then
    echo "Found old plist directory: $OLD_PLIST_DIR"
    
    # Check each plist file for KeepAlive=true
    find "$OLD_PLIST_DIR" -name "*.plist" | while read plist_file; do
        if grep -q "<true/>" "$plist_file" && grep -B 1 "<true/>" "$plist_file" | grep -q "KeepAlive"; then
            echo "Removing problematic plist: $plist_file (has KeepAlive=true)"
            rm -f "$plist_file"
        fi
    done
    
    # Remove the temp directory if empty
    if [ -z "$(ls -A "$OLD_PLIST_DIR" 2>/dev/null)" ]; then
        rmdir "$OLD_PLIST_DIR" 2>/dev/null || true
        print_success "Removed empty temp directory"
    fi
else
    print_success "No old plist directory found"
fi
echo ""

# Step 4: Clean up any other conflicting plist files
print_status "Cleaning up any other conflicting plist files..."
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
find "$LAUNCH_AGENTS_DIR" -name "*clipboard*" -o -name "*monitor*" | while read plist_file; do
    if [ -f "$plist_file" ] && [ "$(basename "$plist_file")" != "com.clipboardmonitor.plist" ] && [ "$(basename "$plist_file")" != "com.clipboardmonitor.menubar.plist" ]; then
        if grep -q "<true/>" "$plist_file" && grep -B 1 "<true/>" "$plist_file" | grep -q "KeepAlive"; then
            echo "Removing conflicting plist: $plist_file (has KeepAlive=true)"
            rm -f "$plist_file"
        fi
    fi
done
print_success "Cleanup completed"
echo ""

# Step 5: Verify cleanup
print_status "Verifying cleanup..."
REMAINING_PROCESSES=$(ps aux | grep -i "ClipboardMonitor" | grep -v grep | grep -v "fix_multiple" || true)
if [ -n "$REMAINING_PROCESSES" ]; then
    print_warning "Some ClipboardMonitor processes still running:"
    echo "$REMAINING_PROCESSES"
else
    print_success "No ClipboardMonitor processes running"
fi

REMAINING_SERVICES=$(launchctl list | grep -i clipboard || true)
if [ -n "$REMAINING_SERVICES" ]; then
    print_warning "Some clipboard services still loaded:"
    echo "$REMAINING_SERVICES"
else
    print_success "No clipboard services loaded"
fi
echo ""

# Step 6: Instructions for next steps
echo -e "${BLUE}🚀 NEXT STEPS:${NC}"
echo "=============="
echo ""
echo "1. 📁 Copy the corrected plist files from the DMG to:"
echo "   ~/Library/LaunchAgents/"
echo "   • com.clipboardmonitor.plist"
echo "   • com.clipboardmonitor.menubar.plist"
echo ""
echo "2. 🔄 Load the corrected services:"
echo "   launchctl load ~/Library/LaunchAgents/com.clipboardmonitor.plist"
echo "   launchctl load ~/Library/LaunchAgents/com.clipboardmonitor.menubar.plist"
echo ""
echo "3. ✅ Verify only 2 processes are running:"
echo "   ps aux | grep ClipboardMonitor"
echo ""
echo -e "${GREEN}The multiple spawning issue should now be resolved!${NC}"
echo ""

echo "Press any key to continue..."
read -n 1 -s
