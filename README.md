# Clipboard Monitor for macOS

A Python script that monitors the macOS clipboard for changes and processes them through modular plugins. This script is designed to run as a background service using `launchd` and features enhanced monitoring capabilities using pyobjc.

## Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/omairaslam/Clipboard-Monitor.git
   cd Clipboard-Monitor/clipboard_monitor
   ```

2. **Install Dependencies**
   ```bash
   ./install_dependencies.sh
   ```

3. **Configure and Install**
   ```bash
   # Update paths in plist files, then:
   cp com.omairaslam.clipboardmonitor.plist ~/Library/LaunchAgents/
   cp com.omairaslam.clipboardmonitor.menubar.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist
   launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.menubar.plist
   ```

## Features

- **Enhanced Clipboard Monitoring**: Uses native macOS APIs for efficient clipboard change detection
- **Multiple History Viewers**: GUI, web browser, and command-line interfaces
- **Modular Plugin System**: Process clipboard content through specialized modules
- **Menu Bar Application**: Control the service and access features through a convenient menu bar icon
- **Markdown Processing**: Automatically convert markdown to rich text format
- **Mermaid Diagram Detection**: Open Mermaid diagrams in the Mermaid Live Editor
- **Code Formatting**: Detect and format code snippets (read-only by default)
- **Clipboard History**: Track and browse your clipboard history with deduplication
- **Security Features**: Input validation and AppleScript injection prevention
- **Path Safety**: Secure tilde expansion with fallback mechanisms

## Documentation

Complete documentation is available in the [`docs/`](clipboard_monitor/docs/) folder:

- **[Main Documentation](clipboard_monitor/docs/readme.md)** - Complete installation and usage guide
- **[Module Development Guide](clipboard_monitor/docs/MODULE_DEVELOPMENT.md)** - Create custom processing modules
- **[Latest Updates](clipboard_monitor/docs/LATEST_UPDATES.md)** - Recent changes and improvements
- **[Project Journey](clipboard_monitor/docs/PROJECT_JOURNEY.md)** - Complete development history
- **[Bug Fixes](clipboard_monitor/docs/FIXES.md)** - Detailed analysis of fixes and improvements
- **[Performance Optimizations](clipboard_monitor/docs/PERFORMANCE_OPTIMIZATIONS.md)** - Performance improvements
- **[Monitoring Methods](clipboard_monitor/docs/MONITORING_METHODS.md)** - Technical details on monitoring approaches
- **[Tilde Expansion Fix](clipboard_monitor/docs/TILDE_EXPANSION_FIX.md)** - Path handling security fix
- **[Module Enable/Disable Fix](clipboard_monitor/docs/MODULE_ENABLE_DISABLE_FIX.md)** - Module configuration system fix

## Quick Reference

### Service Management
```bash
# Start the service
launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist

# Stop the service
launchctl unload ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist

# View logs
tail -f ~/Library/Logs/ClipboardMonitor.out.log
```

### History Viewers
```bash
# GUI viewer
python3 clipboard_monitor/history_viewer.py

# Web viewer (opens in browser)
python3 clipboard_monitor/web_history_viewer.py

# CLI viewer
python3 clipboard_monitor/cli_history_viewer.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/omairaslam/Clipboard-Monitor).
