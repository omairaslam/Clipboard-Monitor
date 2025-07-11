#!/bin/bash
# Emergency restart script for memory leak crisis

echo "🚨 EMERGENCY MEMORY LEAK RESPONSE"
echo "================================="

# Step 1: Kill all clipboard monitor processes
echo "1. Stopping all clipboard monitor processes..."
pkill -f menu_bar_app.py
pkill -f main.py
sleep 2

# Step 2: Clear all memory data files
echo "2. Clearing accumulated memory data..."
rm -f ~/Library/Application\ Support/ClipboardMonitor/memory_data.json
rm -f ~/Library/Application\ Support/ClipboardMonitor/menubar_profile.json
rm -f ~/Library/Application\ Support/ClipboardMonitor/advanced_profile.json
rm -f ~/Library/Application\ Support/ClipboardMonitor/longterm_monitoring.json

# Step 3: Check clipboard history size
echo "3. Checking clipboard history size..."
if [ -f ~/Library/Application\ Support/ClipboardMonitor/clipboard_history.json ]; then
    SIZE=$(ls -lh ~/Library/Application\ Support/ClipboardMonitor/clipboard_history.json | awk '{print $5}')
    echo "   Clipboard history size: $SIZE"
    
    # If history is large, back it up and truncate
    if [ -f ~/Library/Application\ Support/ClipboardMonitor/clipboard_history.json ]; then
        FILESIZE=$(stat -f%z ~/Library/Application\ Support/ClipboardMonitor/clipboard_history.json)
        if [ $FILESIZE -gt 1048576 ]; then  # > 1MB
            echo "   ⚠️  Large history file detected, backing up and truncating..."
            cp ~/Library/Application\ Support/ClipboardMonitor/clipboard_history.json ~/Library/Application\ Support/ClipboardMonitor/clipboard_history_backup.json
            echo "[]" > ~/Library/Application\ Support/ClipboardMonitor/clipboard_history.json
            echo "   ✅ History truncated, backup saved"
        fi
    fi
else
    echo "   No clipboard history file found"
fi

# Step 4: Wait a moment for cleanup
echo "4. Waiting for system cleanup..."
sleep 3

# Step 5: Restart with emergency settings
echo "5. Restarting services with emergency leak prevention..."

# Start main service first
echo "   Starting main service..."
cd "$(dirname "$0")"
python3 main.py &
MAIN_PID=$!
echo "   Main service started (PID: $MAIN_PID)"

# Wait a moment
sleep 2

# Start menu bar app
echo "   Starting menu bar app with emergency settings..."
python3 menu_bar_app.py &
MENU_PID=$!
echo "   Menu bar app started (PID: $MENU_PID)"

# Step 6: Monitor initial memory usage
echo "6. Monitoring initial memory usage..."
sleep 5

python3 -c "
import psutil
import time

print('Initial memory check:')
for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
    try:
        cmdline = proc.info.get('cmdline', [])
        if cmdline:
            cmdline_str = ' '.join(cmdline)
            if 'menu_bar_app.py' in cmdline_str:
                memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                print(f'  Menu Bar App: {memory_mb:.1f} MB')
                if memory_mb > 50:
                    print(f'    ⚠️  Still high - may need manual intervention')
                else:
                    print(f'    ✅ Memory usage looks good')
            elif 'main.py' in cmdline_str and 'clipboard' in cmdline_str.lower():
                memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                print(f'  Main Service: {memory_mb:.1f} MB')
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        continue
"

echo ""
echo "✅ Emergency restart complete!"
echo ""
echo "📋 Next steps:"
echo "1. Monitor memory usage in menu bar: Memory Usage → Current Usage"
echo "2. Keep memory tracking DISABLED"
echo "3. If memory still grows, manually clear clipboard history"
echo "4. Restart monitoring: ./start_monitoring.sh"
echo ""
echo "🚨 If memory exceeds 100MB again, the app will auto-cleanup"
