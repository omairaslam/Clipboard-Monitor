#!/bin/bash
#
# Shared Configuration for Clipboard Monitor Management Scripts
# This file is intended to be sourced by other scripts.
#

# --- Service Configuration ---
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_BACKGROUND="com.clipboardmonitor.service.dev.plist"
PLIST_MENUBAR="com.clipboardmonitor.menubar.dev.plist"

# Note: Service labels for launchctl list are derived from filenames by removing .plist extension
# Use ${PLIST_BACKGROUND%.plist} and ${PLIST_MENUBAR%.plist} when labels are needed

# --- Log Configuration ---
LOG_DIR="$HOME/Library/Logs"
LOG_FILES=(
    "ClipboardMonitor.out.log"
    "ClipboardMonitor.err.log"
    "ClipboardMonitorMenuBar.out.log"
    "ClipboardMonitorMenuBar.err.log"
)

# --- State Flags ---
PAUSE_FLAG_PATH="$HOME/Library/Application Support/ClipboardMonitor/pause_flag"

# --- Colors and Icons ---
# Check if the terminal supports colors using tput for robustness
if tput setaf 1 &> /dev/null; then
    # Modern tput colors
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    RED=$(tput setaf 1)
    NC=$(tput sgr0) # No Color / Reset
else
    # Fallback to empty strings if tput is not available or fails
    GREEN=""
    YELLOW=""
    RED=""
    NC=""
fi

ICON_RESTART="🔄"
ICON_START="▶️"
ICON_STOP="🛑"
ICON_STATUS="📊"
ICON_TRASH="🗑️"
ICON_SUCCESS="✅"
ICON_ERROR="❌"
ICON_RUNNING="🟢"
ICON_PAUSED="⏸️"
ICON_STOPPED="🔴"
ICON_NOT_LOADED="⚪️"