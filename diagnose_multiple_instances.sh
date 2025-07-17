#!/bin/bash

# Comprehensive Diagnostic Script for Multiple ClipboardMonitor Instances
# This script helps identify and fix the multiple spawning issue

echo "🔍 ClipboardMonitor Multiple Instance Diagnostic"
echo "==============================================="
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

# Step 1: Check running processes
print_status "Checking for running ClipboardMonitor processes..."
CLIPBOARD_PROCESSES=$(ps aux | grep -i "ClipboardMonitor\|MenuBar" | grep -v grep | grep -v "diagnose")
if [ -n "$CLIPBOARD_PROCESSES" ]; then
    echo "$CLIPBOARD_PROCESSES"
    PROCESS_COUNT=$(echo "$CLIPBOARD_PROCESSES" | wc -l | tr -d ' ')
    if [ "$PROCESS_COUNT" -gt 2 ]; then
        print_error "Found $PROCESS_COUNT ClipboardMonitor processes (should be max 2)"
    else
        print_success "Found $PROCESS_COUNT ClipboardMonitor processes (normal)"
    fi
else
    print_success "No ClipboardMonitor processes currently running"
fi
echo ""

# Step 2: Check LaunchAgent plist files
print_status "Checking LaunchAgent plist files..."
PLIST_DIR="$HOME/Library/LaunchAgents"
BACKGROUND_PLIST="$PLIST_DIR/com.clipboardmonitor.plist"
MENUBAR_PLIST="$PLIST_DIR/com.clipboardmonitor.menubar.plist"

if [ -f "$BACKGROUND_PLIST" ]; then
    print_success "Background plist exists: $BACKGROUND_PLIST"
    KEEP_ALIVE_BG=$(grep -A 1 "KeepAlive" "$BACKGROUND_PLIST" | tail -1 | grep -o "true\|false")
    echo "   KeepAlive setting: $KEEP_ALIVE_BG"
    if [ "$KEEP_ALIVE_BG" = "true" ]; then
        print_error "KeepAlive=true in background plist (CAUSES MULTIPLE SPAWNING)"
    else
        print_success "KeepAlive=false in background plist (correct)"
    fi
else
    print_warning "Background plist not found: $BACKGROUND_PLIST"
fi

if [ -f "$MENUBAR_PLIST" ]; then
    print_success "Menu bar plist exists: $MENUBAR_PLIST"
    KEEP_ALIVE_MB=$(grep -A 1 "KeepAlive" "$MENUBAR_PLIST" | tail -1 | grep -o "true\|false")
    echo "   KeepAlive setting: $KEEP_ALIVE_MB"
    if [ "$KEEP_ALIVE_MB" = "true" ]; then
        print_error "KeepAlive=true in menu bar plist (CAUSES MULTIPLE SPAWNING)"
    else
        print_success "KeepAlive=false in menu bar plist (correct)"
    fi
else
    print_warning "Menu bar plist not found: $MENUBAR_PLIST"
fi
echo ""

# Step 3: Check launchctl status
print_status "Checking launchctl service status..."
BG_STATUS=$(launchctl list | grep "com.clipboardmonitor" | grep -v menubar || echo "not loaded")
MB_STATUS=$(launchctl list | grep "com.clipboardmonitor.menubar" || echo "not loaded")

echo "Background service: $BG_STATUS"
echo "Menu bar service: $MB_STATUS"
echo ""

# Step 4: Check for old/conflicting plist files
print_status "Checking for old or conflicting plist files..."
OLD_PLISTS=$(find "$PLIST_DIR" -name "*clipboard*" -o -name "*monitor*" 2>/dev/null)
if [ -n "$OLD_PLISTS" ]; then
    echo "Found plist files:"
    echo "$OLD_PLISTS"
else
    print_success "No old plist files found"
fi
echo ""

# Step 5: Check application bundle
print_status "Checking application bundle..."
APP_PATH="/Applications/Clipboard Monitor.app"
if [ -d "$APP_PATH" ]; then
    print_success "Application bundle exists: $APP_PATH"
    
    # Check internal plist files
    INTERNAL_BG_PLIST="$APP_PATH/Contents/Resources/com.clipboardmonitor.plist"
    INTERNAL_MB_PLIST="$APP_PATH/Contents/Resources/com.clipboardmonitor.menubar.plist"
    
    if [ -f "$INTERNAL_BG_PLIST" ]; then
        INTERNAL_KEEP_ALIVE_BG=$(grep -A 1 "KeepAlive" "$INTERNAL_BG_PLIST" | tail -1 | grep -o "true\|false")
        echo "   Internal background plist KeepAlive: $INTERNAL_KEEP_ALIVE_BG"
    fi
    
    if [ -f "$INTERNAL_MB_PLIST" ]; then
        INTERNAL_KEEP_ALIVE_MB=$(grep -A 1 "KeepAlive" "$INTERNAL_MB_PLIST" | tail -1 | grep -o "true\|false")
        echo "   Internal menu bar plist KeepAlive: $INTERNAL_KEEP_ALIVE_MB"
    fi
else
    print_error "Application bundle not found: $APP_PATH"
fi
echo ""

# Step 6: Recommendations
echo -e "${BLUE}🔧 RECOMMENDATIONS:${NC}"
echo "==================="

if [ "$KEEP_ALIVE_BG" = "true" ] || [ "$KEEP_ALIVE_MB" = "true" ]; then
    print_error "CRITICAL: KeepAlive=true detected in plist files"
    echo ""
    echo "TO FIX MULTIPLE SPAWNING:"
    echo "1. Stop all services:"
    echo "   launchctl unload '$BACKGROUND_PLIST'"
    echo "   launchctl unload '$MENUBAR_PLIST'"
    echo ""
    echo "2. Replace plist files with corrected versions from DMG"
    echo ""
    echo "3. Reload services:"
    echo "   launchctl load '$BACKGROUND_PLIST'"
    echo "   launchctl load '$MENUBAR_PLIST'"
else
    print_success "KeepAlive settings are correct"
    echo ""
    echo "If still experiencing multiple instances:"
    echo "1. Kill all processes: pkill -f ClipboardMonitor"
    echo "2. Unload services and reload"
    echo "3. Check for manual app launches"
fi

echo ""
echo "Press any key to continue..."
read -n 1 -s
