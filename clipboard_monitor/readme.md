# Clipboard Monitor for macOS

A Python script that monitors the macOS clipboard for changes and processes them through modular plugins. This script is designed to run as a background service using `launchd` and features enhanced monitoring capabilities using pyobjc.

## Features

- **Enhanced Clipboard Monitoring**: Uses native macOS APIs for efficient clipboard change detection
- **Modular Plugin System**: Process clipboard content through specialized modules with robust error handling
- **Menu Bar Application**: Control the service and access features through a convenient menu bar icon with comprehensive configuration options
- **Clipboard History**: Track and browse your clipboard history with deduplication
- **Markdown Processing**: Automatically convert markdown to rich text with comprehensive formatting support
- **Mermaid Diagram Detection**: Open Mermaid diagrams in the Mermaid Live Editor with multiple diagram types
- **Code Formatting**: Automatically format code snippets with language detection
- **Thread Safety**: Prevent race conditions and processing loops with advanced content tracking
- **Loop Prevention**: Intelligent content hashing to prevent infinite processing cycles
- **Robust Error Handling**: Comprehensive exception handling with graceful degradation
- **Security Features**: Input validation and AppleScript injection prevention
- **Configurable Settings**: Customize behavior with flexible configuration options
- **Performance Optimized**: Efficient polling with consecutive error tracking and automatic recovery

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/clipboard-monitor.git
   cd clipboard_monitor
   ```

2. **Install Dependencies**
   This script requires the following Python libraries:
   * `pyperclip` - Cross-platform clipboard access
   * `rich` - Rich console output and logging
   * `pyobjc-framework-Cocoa` - macOS integration for enhanced clipboard monitoring
   * `rumps` - Menu bar application support

   **Easy Installation (Recommended):**
   Use the provided installation script:
   ```bash
   cd clipboard_monitor
   ./install_dependencies.sh
   ```

   **Manual Installation:**
   The project includes a `requirements.txt` file with all dependencies:
   ```bash
   python3 -m pip install --user -r requirements.txt
   ```

3. **Configure the LaunchAgent**
   Update the paths in `com.omairaslam.clipboardmonitor.plist`:
   - Replace `/path/to/your/venv/bin/python` with your Python interpreter path
   - Replace `/path/to/your/project/main.py` with the absolute path to the main script
   - Replace `/path/to/your/project/` with your project directory

4. **Install the LaunchAgent**
   ```bash
   cp com.omairaslam.clipboardmonitor.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist
   ```

## Modules

The Clipboard Monitor includes several processing modules:

### Markdown Module
Detects and converts markdown content to rich text format (RTF). **Modifies clipboard content** when enabled (default: enabled).

### Mermaid Module
Detects Mermaid diagram syntax, sanitizes content for safe processing, and opens it in the Mermaid Live Editor. **Never modifies clipboard content** - only opens browser.

### History Module
Tracks clipboard history with timestamps and content hashing for deduplication. **Never modifies clipboard content** - read-only tracking.

### Code Formatter Module
Detects and formats code snippets using language-specific formatters. **Read-only by default** - only detects and notifies, doesn't modify clipboard unless explicitly enabled.

## 🛡️ Clipboard Safety

**Your clipboard content is protected!** The Clipboard Monitor follows strict safety principles:

### **Safe by Default**
- ✅ **Plain text, URLs, emails, JSON** - Never modified
- ✅ **Code snippets** - Only detected and notified (read-only by default)
- ✅ **Mermaid diagrams** - Opens browser, never modifies clipboard
- ✅ **Unknown content** - Always left unchanged

### **Configurable Modifications**
Only specific content types can modify your clipboard, and it's fully configurable:

- **Markdown → RTF**: Enabled by default (main feature)
- **Code Formatting**: Disabled by default (can be enabled)
- **All other content**: Never modified

### **User Control**
Access clipboard modification settings through:
**Menu Bar** → **Preferences** → **Clipboard Modification**

- Toggle markdown RTF conversion on/off
- Enable/disable code formatter clipboard modification
- Changes apply immediately with automatic service restart

## Menu Bar App

The Clipboard Monitor includes a menu bar app that allows you to:

- **Service Status**: Check service status (running/stopped/paused, enhanced/polling mode)
- **Service Control**: Start, stop, and restart the service
- **Pause/Resume**: Temporarily pause monitoring without stopping the service
- **Log Management**: View output and error logs, clear logs
- **Module Control**: Enable/disable specific modules
- **Clipboard History**: Access clipboard history
- **Configuration**: Configure all application settings through user-friendly interface
- **Enhanced Notifications**: Reliable notification system with AppleScript integration

### Installing the Menu Bar App

1. Make sure you've installed the required dependencies:
   ```bash
   ./install_dependencies.sh
   ```

2. Update the paths in `com.omairaslam.clipboardmonitor.menubar.plist`:
   - Replace `/path/to/your/venv/bin/python` with your Python interpreter path
   - Replace `/path/to/your/project/menu_bar_app.py` with the absolute path to the menu bar script
   - Replace `/path/to/your/project/` with your project directory

3. Copy the plist file to your LaunchAgents directory:
   ```bash
   cp com.omairaslam.clipboardmonitor.menubar.plist ~/Library/LaunchAgents/
   ```

4. Load the LaunchAgent:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.menubar.plist
   ```

## Configuration

The application can be configured in two convenient ways:

### 1. Menu Bar Configuration (Recommended)

All settings can be easily configured through the menu bar application:

#### **Preferences Menu**
- **General Settings**: Debug mode, notification title, polling intervals
- **Performance Settings**: Lazy loading, adaptive checking, memory optimization
- **History Settings**: Max items, content length, file location
- **Security Settings**: Clipboard sanitization, size limits
- **Clipboard Modification**: Control which modules can modify clipboard content
- **Configuration Management**: Reset, export, import, and view settings

**Access**: Click the menu bar icon → Preferences → Choose your setting category

**Benefits**:
- No file editing required
- Automatic service restart after changes
- Input validation and user-friendly dialogs
- Real-time configuration updates

### 2. Manual Configuration File

You can also manually edit the `config.json` file:

```json
{
  "general": {
    "polling_interval": 1.0,
    "enhanced_check_interval": 0.1,
    "notification_title": "Clipboard Monitor",
    "debug_mode": false
  },
  "performance": {
    "lazy_module_loading": true,
    "adaptive_checking": true,
    "memory_optimization": true,
    "process_large_content": true,
    "max_module_execution_time": 500
  },
  "modules": {
    "markdown_module": true,
    "mermaid_module": true,
    "history_module": true,
    "code_formatter_module": true,
    "markdown_modify_clipboard": true,
    "code_formatter_modify_clipboard": false
  },
  "history": {
    "max_items": 100,
    "max_content_length": 10000,
    "save_location": "~/Library/Application Support/ClipboardMonitor/clipboard_history.json"
  },
  "security": {
    "sanitize_clipboard": true,
    "max_clipboard_size": 10485760
  }
}
```

**Note**: Manual changes require service restart to take effect.

## 🎛️ Pause/Resume Monitoring

The Clipboard Monitor includes a convenient pause/resume feature that allows you to temporarily stop monitoring without shutting down the service:

### **How It Works**
- **Pause**: Temporarily stops clipboard monitoring while keeping the service running
- **Resume**: Instantly resumes monitoring from where it left off
- **No Service Restart**: Much faster than stopping/starting the entire service
- **State Persistence**: Pause state is maintained across menu bar app restarts

### **Usage**
1. **Click the menu bar icon** (📋)
2. **Select "Pause Monitoring"** to pause
3. **Select "Resume Monitoring"** to resume
4. **Status indicator** shows current state (Running/Paused)

### **Benefits**
- ✅ **Instant toggle** - No waiting for service restart
- ✅ **Preserves state** - All modules and settings remain loaded
- ✅ **Battery saving** - Reduces CPU usage when not needed
- ✅ **Privacy control** - Temporarily disable monitoring for sensitive work
- ✅ **Clear feedback** - Status updates and notifications confirm state changes

### **Technical Implementation**
- Uses a pause flag file for communication between menu bar and service
- Both enhanced and polling monitoring modes respect the pause state
- Automatic cleanup when service stops
- Thread-safe implementation with proper state management

## 🔔 Enhanced Notifications

The application features a robust notification system with multiple fallback mechanisms:

### **Notification Features**
- **AppleScript Integration**: Direct macOS notification system access
- **Dual Notification System**: Primary AppleScript + fallback rumps notifications
- **Security Hardened**: Input sanitization prevents AppleScript injection
- **Customizable Titles**: Configure notification titles through menu bar
- **Context-Aware**: Different notifications for enhanced vs. polling mode

### **Notification Types**
- **Clipboard Changes**: "Clipboard changed (enhanced)!" or "Clipboard changed (polling)!"
- **Service Control**: Start, stop, restart confirmations
- **Pause/Resume**: Clear feedback when monitoring is paused/resumed
- **Module Actions**: Markdown conversion, Mermaid detection, etc.
- **Configuration Changes**: Settings updates and validation results

### **Reliability Features**
- **Timeout Protection**: Prevents hanging on notification failures
- **Error Logging**: Failed notifications are logged for debugging
- **Fallback Mechanisms**: Multiple notification methods ensure delivery
- **Thread Safety**: Proper main thread handling for macOS notifications

## Quick Reference

### Service Management

```bash
# Start the service
launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist

# Stop the service
launchctl unload ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist

# Restart the service
launchctl unload ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist
launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist

# View logs
tail -f ~/Library/Logs/ClipboardMonitor.out.log
tail -f ~/Library/Logs/ClipboardMonitor.err.log
```

### Dependencies

```bash
# Run the installation script (if available)
./install_dependencies.sh

# Or install manually
python3 -m pip install --user -r requirements.txt
```

## Troubleshooting Tips

### Service Not Starting
- Check the error logs: `tail -f ~/Library/Logs/ClipboardMonitor.err.log`
- Verify the paths in your plist file are correct
- Ensure Python and all dependencies are installed
- Try running the script manually to see any errors: `python3 main.py`

### Enhanced Monitoring Not Working
- Verify pyobjc is installed: `pip3 list | grep pyobjc`
- Check if the service is running in polling mode
- Try reinstalling pyobjc: `pip3 install --upgrade pyobjc-framework-Cocoa`
- Check the logs for import errors

### Module Not Processing Content
- Check if the module is enabled in config.json
- Verify the module's process function is working correctly
- Check the logs for any errors related to the module
- Try running the module directly for testing

## Creating Custom Modules

See the [Module Development Guide](MODULE_DEVELOPMENT.md) for information on creating your own processing modules.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
