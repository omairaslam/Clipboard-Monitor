# ClipboardMonitor Development Services - Troubleshooting Guide

## 🎯 Purpose

These development plist files point directly to the Python files in the project folder, allowing us to troubleshoot the unified dashboard detection issue without the complexity of PKG installation.

## 📁 Files Created

- `com.clipboardmonitor.service.dev.plist` - Main service plist (points to `main.py`)
- `com.clipboardmonitor.menubar.dev.plist` - Menu bar app plist (points to `menu_bar_app.py`)
- `install_dev_services.sh` - Installation script
- `uninstall_dev_services.sh` - Uninstallation script

## 🚀 Installation Steps

1. **First, uninstall existing PKG services:**
   ```bash
   # Stop current PKG services
   sudo launchctl unload /Library/LaunchDaemons/com.clipboardmonitor.service.plist 2>/dev/null || true
   launchctl unload ~/Library/LaunchAgents/com.clipboardmonitor.menubar.plist 2>/dev/null || true
   ```

2. **Install development services:**
   ```bash
   ./install_dev_services.sh
   ```

3. **Verify installation:**
   ```bash
   # Check if services are running
   sudo launchctl list | grep com.clipboardmonitor.service.dev
   launchctl list | grep com.clipboardmonitor.menubar.dev
   
   # Check Python processes
   ps aux | grep -E "(main\.py|menu_bar_app.py)" | grep -v grep
   ```

## 🔍 Testing the Unified Dashboard

Once the development services are running:

1. **Test the unified dashboard:**
   ```bash
   python3 unified_memory_dashboard.py --auto-start
   ```

2. **Check the API response:**
   ```bash
   curl -s http://localhost:8001/api/memory | jq
   ```

3. **Look for the Python processes in the API response:**
   - Should see processes with `main.py` and `menu_bar_app.py` in cmdline
   - Should see non-zero `peak_service_memory` and `peak_menubar_memory`

## 📊 Expected Results

With Python processes, the unified dashboard should:

✅ **Detect processes correctly:**
- `main.py` process → classified as Main Service
- `menu_bar_app.py` process → classified as Menu Bar App

✅ **Show memory values:**
- `peak_service_memory` > 0
- `peak_menubar_memory` > 0
- `peak_total_memory` > 0

✅ **API response includes:**
```json
{
  "clipboard": {
    "processes": [
      {
        "pid": 12345,
        "name": "Python",
        "cmdline_snippet": "main.py",
        "process_type": "service"
      },
      {
        "pid": 12346,
        "name": "Python", 
        "cmdline_snippet": "menu_bar_app.py",
        "process_type": "menubar"
      }
    ]
  },
  "peak_service_memory": 25.0,
  "peak_menubar_memory": 80.0
}
```

## 🐛 Troubleshooting

### If services don't start:
```bash
# Check logs
tail -f ~/Library/Logs/ClipboardMonitor*.log

# Check launchctl status
sudo launchctl list | grep clipboardmonitor
launchctl list | grep clipboardmonitor
```

### If processes aren't detected:
```bash
# Verify Python processes are running
ps aux | grep -E "(main\.py|menu_bar_app.py)" | grep -v grep

# Test psutil detection manually
python3 -c "
import psutil
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    cmdline = proc.info.get('cmdline', [])
    if cmdline and any('main.py' in arg or 'menu_bar_app.py' in arg for arg in cmdline):
        print(f'Found: PID {proc.info[\"pid\"]}, Name: {proc.info[\"name\"]}, Cmdline: {cmdline}')
"
```

## 🧹 Cleanup

When troubleshooting is complete:

```bash
# Uninstall development services
./uninstall_dev_services.sh

# Reinstall PKG services if needed
# (Use the PKG installer)
```

## 🎯 Next Steps

1. **If development services work:** The issue is with PKG installation/PyInstaller detection
2. **If development services don't work:** The issue is with the unified dashboard detection logic
3. **Once fixed:** Move to PKG creation with proper detection for both Python and PyInstaller processes
