#!/bin/bash

# Clipboard Monitor Menu Bar Management Script
# This script helps manage menu bar app instances to prevent duplicates

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MENU_BAR_SCRIPT="$SCRIPT_DIR/menu_bar_app.py"

show_status() {
    echo "🔍 Clipboard Monitor Status"
    echo "=========================="
    
    # Check launchd services
    echo "📋 LaunchD Services:"
    launchctl list | grep -i clipboard || echo "   No clipboard services found"
    
    echo ""
    echo "🖥️  Menu Bar App Processes:"
    ps aux | grep menu_bar_app | grep -v grep || echo "   No menu bar app processes found"
    
    echo ""
    echo "⚙️  Main Service Processes:"
    ps aux | grep "main.py" | grep -v grep || echo "   No main service processes found"
    
    echo ""
    echo "📊 Dashboard Processes:"
    ps aux | grep "unified_memory_dashboard" | grep -v grep || echo "   No dashboard processes found"
}

kill_all_menu_bars() {
    echo "🛑 Killing all menu bar app instances..."
    
    # Kill all menu bar app processes
    pkill -f menu_bar_app.py
    
    # Stop and unload the menu bar service if it exists
    launchctl stop com.clipboardmonitor.menubar.dev 2>/dev/null
    launchctl unload ~/Library/LaunchAgents/com.clipboardmonitor.menubar.dev.plist 2>/dev/null
    
    echo "✅ All menu bar app instances stopped"
}

start_single_menu_bar() {
    echo "🚀 Starting single menu bar app instance..."
    
    # First, make sure no instances are running
    kill_all_menu_bars
    
    # Wait a moment for processes to fully terminate
    sleep 2
    
    # Start a single instance
    cd "$SCRIPT_DIR"
    python3 "$MENU_BAR_SCRIPT" &
    
    echo "✅ Single menu bar app instance started"
    echo "💡 Check the menu bar for the Clipboard Monitor icon"
}

restart_clean() {
    echo "🔄 Restarting with clean single instance..."
    kill_all_menu_bars
    sleep 2
    start_single_menu_bar
}

case "$1" in
    "status")
        show_status
        ;;
    "kill")
        kill_all_menu_bars
        ;;
    "start")
        start_single_menu_bar
        ;;
    "restart")
        restart_clean
        ;;
    *)
        echo "🔧 Clipboard Monitor Menu Bar Management"
        echo "======================================="
        echo ""
        echo "Usage: $0 {status|kill|start|restart}"
        echo ""
        echo "Commands:"
        echo "  status   - Show current status of all clipboard processes"
        echo "  kill     - Kill all menu bar app instances"
        echo "  start    - Start a single clean menu bar app instance"
        echo "  restart  - Kill all instances and start fresh"
        echo ""
        echo "Examples:"
        echo "  $0 status    # Check what's running"
        echo "  $0 restart   # Clean restart (recommended)"
        echo ""
        exit 1
        ;;
esac
