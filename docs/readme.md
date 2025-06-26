# 📋 Clipboard Monitor for macOS

<div align="center">

![macOS](https://img.shields.io/badge/macOS-000000?style=for-the-badge&logo=apple&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

**🚀 A powerful Python script that monitors the macOS clipboard for changes and processes them through modular plugins**

*Designed to run as a background service using `launchd` with enhanced monitoring capabilities using pyobjc*

</div>

---

## ✨ Features

### 🔍 **Core Monitoring**
- 🎯 **Enhanced Clipboard Monitoring**: Uses native macOS APIs for efficient clipboard change detection
- 🧩 **Modular Plugin System**: Process clipboard content through specialized modules with robust error handling
- 🍎 **Menu Bar Application**: Control the service and access features through a convenient menu bar icon

### 📚 **History & Viewers**
- 🕒 **Multiple History Viewers**: Access clipboard history through GUI, web browser, or command-line interfaces
- 💾 **Clipboard History**: Track and browse your clipboard history with deduplication and configurable limits

### 🛠️ **Content Processing**
- 📝 **Markdown Processing**: Automatically convert markdown to rich text with comprehensive formatting support
- 🎨 **Mermaid Diagram Detection**: Open Mermaid diagrams in the Mermaid Live Editor with multiple diagram types
- 💻 **Code Formatting**: Automatically format code snippets with language detection (read-only by default)

### 🔒 **Security & Performance**
- 🧵 **Thread Safety**: Prevent race conditions and processing loops with advanced content tracking
- 🔄 **Loop Prevention**: Intelligent content hashing to prevent infinite processing cycles
- 🛡️ **Robust Error Handling**: Comprehensive exception handling with graceful degradation
- 🔐 **Security Features**: Input validation and AppleScript injection prevention
- 📁 **Path Safety**: Secure tilde expansion with fallback mechanisms for all file operations

### ⚙️ **Configuration & Utilities**
- 🔧 **Shared Utilities**: Centralized utility functions for notifications, validation, and content tracking
- 🎛️ **Configurable Settings**: Customize behavior with flexible configuration options through menu bar or config file
- ⚡ **Performance Optimized**: Efficient polling with consecutive error tracking and automatic recovery

## 🚀 Installation

### 📥 **Step 1: Clone the Repository**
```bash
git clone https://github.com/yourusername/clipboard-monitor.git
cd clipboard_monitor
```

### 📦 **Step 2: Install Dependencies**

<details>
<summary><b>📋 Required Python Libraries</b></summary>

| Library | Purpose | Badge |
|---------|---------|-------|
| `pyperclip` | Cross-platform clipboard access | ![PyPI](https://img.shields.io/pypi/v/pyperclip?color=blue) |

| `pyobjc-framework-Cocoa` | macOS integration for enhanced monitoring | ![PyPI](https://img.shields.io/pypi/v/pyobjc-framework-Cocoa?color=orange) |
| `rumps` | Menu bar application support | ![PyPI](https://img.shields.io/pypi/v/rumps?color=purple) |

</details>

#### 🎯 **Easy Installation (Recommended)**
```bash
cd clipboard_monitor
./install_dependencies.sh
```

#### 🔧 **Manual Installation**
```bash
python3 -m pip install --user -r requirements.txt
```

### ⚙️ **Step 3: Configure the LaunchAgent**
Update the paths in `com.omairaslam.clipboardmonitor.plist`:
- 🐍 Replace `/path/to/your/venv/bin/python` with your Python interpreter path
- 📄 Replace `/path/to/your/project/main.py` with the absolute path to the main script
- 📁 Replace `/path/to/your/project/` with your project directory

### 🔄 **Step 4: Install the LaunchAgent**
```bash
cp com.omairaslam.clipboardmonitor.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist
```

## 🧩 Modules

<div align="center">

**🔧 The Clipboard Monitor includes several specialized processing modules**

</div>

| Module | Icon | Function | Clipboard Modification | Status |
|--------|------|----------|----------------------|--------|
| **Markdown** | 📝 | Converts markdown to rich text format (RTF) | ✅ **Modifies** (default: enabled) | ![Status](https://img.shields.io/badge/Status-Active-green) |
| **Mermaid** | 🎨 | Opens Mermaid diagrams in Live Editor | ❌ **Read-only** (opens browser) | ![Status](https://img.shields.io/badge/Status-Active-green) |
| **History** | 🕒 | Tracks clipboard history with timestamps | ❌ **Read-only** (tracking only) | ![Status](https://img.shields.io/badge/Status-Active-green) |
| **Code Formatter** | 💻 | Detects and formats code snippets | ⚠️ **Read-only by default** (configurable) | ![Status](https://img.shields.io/badge/Status-Active-green) |

### 📝 **Markdown Module**
- 🎯 **Purpose**: Detects and converts markdown content to rich text format (RTF)
- ✏️ **Behavior**: **Modifies clipboard content** when enabled
- 🔧 **Default**: Enabled

### 🎨 **Mermaid Module**
- 🎯 **Purpose**: Detects Mermaid diagram syntax and opens in Live Editor
- 🔒 **Behavior**: **Never modifies clipboard content** - only opens browser
- 🛡️ **Security**: Sanitizes content for safe processing

### 🕒 **History Module**
- 🎯 **Purpose**: Tracks clipboard history with timestamps and content hashing
- 📚 **Features**: Deduplication and configurable limits
- 🔒 **Behavior**: **Never modifies clipboard content** - read-only tracking

### 💻 **Code Formatter Module**
- 🎯 **Purpose**: Detects and formats code snippets using language-specific formatters
- ⚙️ **Behavior**: **Read-only by default** - only detects and notifies
- 🔧 **Configuration**: Can be enabled to modify clipboard content

## 📚 History Viewers

<div align="center">

**🎯 Three powerful ways to access your clipboard history**

</div>

| Viewer | Interface | Best For | Key Features |
|--------|-----------|----------|--------------|
| 🖥️ **GUI** | Native macOS | Desktop users | Real-time updates, preview pane |
| 🌐 **Web** | Browser-based | Cross-device access | Responsive design, export options |
| 💻 **CLI** | Terminal | Developers | Scriptable, minimal resources |

---

### 🖥️ **GUI History Viewer** (`history_viewer.py`)

<details>
<summary><b>🎯 Perfect for desktop users who prefer native interfaces</b></summary>

#### ✨ **Features**
- 🍎 **Native macOS Interface**: Clean, native Tkinter-based GUI
- 🔄 **Real-time Updates**: Automatically refreshes when new items are added
- 👁️ **Content Preview**: Click any item to see full content in preview pane
- 📋 **Copy to Clipboard**: Double-click or use button to copy items back
- 🗑️ **Delete Items**: Remove unwanted items from history
- 🧹 **Clear History**: Clear all clipboard history with confirmation dialog
- ⌨️ **Keyboard Shortcuts**: Navigate and interact using keyboard
- 🪟 **Window Management**: Always appears on top with proper focus handling

</details>

---

### 🌐 **Web History Viewer** (`web_history_viewer.py`)

<details>
<summary><b>🌍 Browser-based interface for cross-device access</b></summary>

#### ✨ **Features**
- 🌐 **Browser-based Interface**: Opens in your default web browser
- 📱 **Responsive Design**: Works on any screen size with modern styling
- 🔍 **Search and Filter**: Find specific items quickly
- 📤 **Export Options**: Save history to various formats
- 🧹 **Clear History**: Clear all clipboard history with instructions
- 🔗 **Shareable**: Access from any device on the same network
- 🔄 **Auto-refresh**: Automatically updates when clipboard changes

</details>

---

### 💻 **CLI History Viewer** (`cli_history_viewer.py`)

<details>
<summary><b>⚡ Terminal interface for developers and power users</b></summary>

#### ✨ **Features**
- 💻 **Terminal Interface**: Perfect for command-line workflows
- 📄 **Plain Text Output**: Standard output with timestamps and log levels (no colorized or rich formatting)
- 📄 **Pagination**: Handle large histories efficiently
- ⚡ **Quick Actions**: Copy, delete, and search from terminal
- 🧹 **Clear History**: Clear all clipboard history with confirmation prompt
- 🔧 **Scriptable**: Can be integrated into shell scripts and automation
- 🪶 **Minimal Resource Usage**: Lightweight for server environments

</details>

## 🛡️ Clipboard Safety

<div align="center">

![Security](https://img.shields.io/badge/Security-First-red?style=for-the-badge&logo=shield&logoColor=white)
![Privacy](https://img.shields.io/badge/Privacy-Protected-blue?style=for-the-badge&logo=lock&logoColor=white)

**🔒 Your clipboard content is protected! The Clipboard Monitor follows strict safety principles**

</div>

---

### 🟢 **Safe by Default**

<table>
<tr>
<td align="center">

**✅ NEVER MODIFIED**

</td>
</tr>
<tr>
<td>

- 📝 **Plain text, URLs, emails, JSON** - Never modified
- 💻 **Code snippets** - Only detected and notified (read-only by default)
- 🎨 **Mermaid diagrams** - Opens browser, never modifies clipboard
- ❓ **Unknown content** - Always left unchanged

</td>
</tr>
</table>

---

### ⚙️ **Configurable Modifications**

<table>
<tr>
<td align="center">

**🎛️ FULLY CONFIGURABLE**

</td>
</tr>
<tr>
<td>

Only specific content types can modify your clipboard:

| Content Type | Default State | Configurable |
|--------------|---------------|--------------|
| 📝 **Markdown → RTF** | ✅ Enabled | ✅ Yes |
| 💻 **Code Formatting** | ❌ Disabled | ✅ Yes |
| 🌐 **All other content** | ❌ Never modified | ❌ No |

</td>
</tr>
</table>

---

### 🎛️ **User Control**

<div align="center">

**🔧 Access clipboard modification settings through:**

**Menu Bar** → **Preferences** → **Clipboard Modification**

</div>

#### 🎯 **Available Controls**
- 🔄 Toggle markdown RTF conversion on/off
- 💻 Enable/disable code formatter clipboard modification
- ⚡ Changes apply immediately with automatic service restart

## 🍎 Menu Bar App

<div align="center">

![Menu Bar](https://img.shields.io/badge/Menu_Bar-Native-blue?style=for-the-badge&logo=apple&logoColor=white)
![Control](https://img.shields.io/badge/Control-Center-green?style=for-the-badge&logo=settings&logoColor=white)

**🎛️ Complete control center for your Clipboard Monitor**

</div>

---

### 🎯 **Core Features**

<table>
<tr>
<td width="50%">

#### 📊 **Service Management**
- 🔍 **Service Status**: Check running/stopped/paused state
- 🎚️ **Enhanced/Polling Mode**: Monitor current mode
- ▶️ **Service Control**: Start, stop, and restart
- ⏸️ **Pause/Resume**: Temporary monitoring control

- 🕒 **Recent Clipboard Items**: Now always appears just before "View Clipboard History" in the menu for quick access.
- 🧹 **Clear History**: Available in both "Recent Clipboard Items" and "View Clipboard History" menus, with confirmation and error handling.
- 🐞 **Improved Debugging**: Debug mode and configuration changes are now more robust and reflected in the menu.

</td>
<td width="50%">

#### 📋 **History Access**
- 🕒 **Recent History**: Quick access to last 10 items
- 🖱️ **One-Click Copy**: Click any item to copy
- 🧹 **Clear History**: Direct access from menu bar
- 👁️ **Multiple Viewers**: GUI, Web, and CLI options

</td>
</tr>
</table>

---

### 🔧 **Advanced Controls**

| Feature | Icon | Description |
|---------|------|-------------|
| **Log Management** | 📝 | View output and error logs, clear logs |
| **Module Control** | 🧩 | Enable/disable specific modules |
| **Configuration** | ⚙️ | User-friendly settings interface |
| **Notifications** | 🔔 | AppleScript integration for reliable alerts |

---

### 📚 **History Viewer Options**

<details>
<summary><b>🎯 Multiple ways to access your clipboard history</b></summary>

| Viewer | Access Method | Best For |
|--------|---------------|----------|
| 🖥️ **GUI Viewer** | Menu Bar → View History → GUI | Desktop users |
| 🌐 **Web Viewer** | Menu Bar → View History → Web | Cross-device access |
| 💻 **CLI Viewer** | Menu Bar → View History → CLI | Developers |
| 🕒 **Recent Items** | Menu Bar → Recent Items | Quick access |

</details>

---

## 🛠️ Troubleshooting Enhanced vs Polling Mode

If the Clipboard Monitor runs in polling mode instead of enhanced mode (even though all dependencies are installed):

1. Go to **System Settings** → **Privacy & Security** → **Full Disk Access**.
2. Find the entry for your `python3` service (or the Python interpreter used by Clipboard Monitor).
3. **Revoke Full Disk Access** for this Python service.
4. **Re-add Full Disk Access** by clicking the `+` button and selecting the same Python interpreter again.
5. Restart the Clipboard Monitor service.

> This step resolves cases where macOS security prevents enhanced clipboard monitoring even when all dependencies are installed.

### 🚀 **Installing the Menu Bar App**

<div align="center">

**📋 Follow these steps to set up your menu bar control center**

</div>

#### **Step 1: Install Dependencies** 📦
```bash
./install_dependencies.sh
```

#### **Step 2: Configure Paths** ⚙️
Update the paths in `com.omairaslam.clipboardmonitor.menubar.plist`:
- 🐍 Replace `/path/to/your/venv/bin/python` with your Python interpreter path
- 📄 Replace `/path/to/your/project/menu_bar_app.py` with the absolute path to the menu bar script
- 📁 Replace `/path/to/your/project/` with your project directory

#### **Step 3: Install LaunchAgent** 📋
```bash
cp com.omairaslam.clipboardmonitor.menubar.plist ~/Library/LaunchAgents/
```

#### **Step 4: Load LaunchAgent** ▶️
```bash
launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.menubar.plist
```

<div align="center">

✅ **Your menu bar app is now ready!** Look for the 📋 icon in your menu bar.

</div>

## ⚙️ Configuration

<div align="center">

![Configuration](https://img.shields.io/badge/Configuration-Flexible-orange?style=for-the-badge&logo=gear&logoColor=white)
![User Friendly](https://img.shields.io/badge/User_Friendly-Interface-green?style=for-the-badge&logo=heart&logoColor=white)

**🎛️ Two convenient ways to configure your Clipboard Monitor**

</div>

---

### 🥇 **Method 1: Menu Bar Configuration** *(Recommended)*

<table>
<tr>
<td align="center">

**🎯 Easy, visual configuration through the menu bar**

</td>
</tr>
</table>

#### 🎛️ **Preferences Categories**

| Category | Icon | Settings |
|----------|------|----------|
| **General** | ⚙️ | Debug mode, notification title, polling intervals |
| **Performance** | ⚡ | Lazy loading, adaptive checking, memory optimization |
| **History** | 📚 | Max items, content length, file location |
| **Security** | 🔒 | Clipboard sanitization, size limits |
| **Clipboard Modification** | ✏️ | Control which modules can modify clipboard content |
| **Configuration Management** | 🔧 | Reset, export, import, and view settings |

#### 🎯 **Access Path**
```
📋 Menu Bar Icon → Preferences → Choose Category
```

#### ✨ **Benefits**
- ✅ No file editing required
- 🔄 Automatic service restart after changes
- ✔️ Input validation and user-friendly dialogs
- ⚡ Real-time configuration updates

---

### 🔧 **Method 2: Manual Configuration File**

<table>
<tr>
<td align="center">

**📝 Direct editing of the `config.json` file**

</td>
</tr>
</table>

<details>
<summary><b>📋 View Complete Configuration Schema</b></summary>

```json
{
  "general": {
    "polling_interval": 1.0,
    "enhanced_check_interval": 0.1,
    "idle_check_interval": 1.0,
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

</details>

> ⚠️ **Note**: Manual changes require service restart to take effect.

## ⏸️ Pause/Resume Monitoring

<div align="center">

![Pause](https://img.shields.io/badge/Pause-Control-orange?style=for-the-badge&logo=pause&logoColor=white)
![Resume](https://img.shields.io/badge/Resume-Control-green?style=for-the-badge&logo=play&logoColor=white)

**🎛️ Convenient pause/resume feature for temporary monitoring control**

</div>

---

### 🔄 **How It Works**

<table>
<tr>
<td width="50%">

#### ⏸️ **Pause**
- 🛑 Temporarily stops clipboard monitoring
- 🔄 Keeps the service running
- 💾 Preserves all loaded modules

</td>
<td width="50%">

#### ▶️ **Resume**
- ⚡ Instantly resumes monitoring
- 🚀 No service restart required
- 📍 Continues from where it left off

</td>
</tr>
</table>

---

### 🎯 **Usage Steps**

```
1. 📋 Click the menu bar icon
2. ⏸️ Select "Pause Monitoring" to pause
3. ▶️ Select "Resume Monitoring" to resume
4. 📊 Status indicator shows current state
```

---

### ✨ **Benefits**

| Benefit | Icon | Description |
|---------|------|-------------|
| **Instant Toggle** | ⚡ | No waiting for service restart |
| **Preserves State** | 💾 | All modules and settings remain loaded |
| **Battery Saving** | 🔋 | Reduces CPU usage when not needed |
| **Privacy Control** | 🔒 | Temporarily disable for sensitive work |
| **Clear Feedback** | 📢 | Status updates and notifications |

---

### 🔧 **Technical Implementation**

<details>
<summary><b>🛠️ Under the Hood</b></summary>

- 📁 Uses a pause flag file for communication between menu bar and service
- 🎯 Both enhanced and polling monitoring modes respect the pause state
- 🧹 Automatic cleanup when service stops
- 🧵 Thread-safe implementation with proper state management

</details>

## 🗑️ Clear History Functionality

<div align="center">

![Clear](https://img.shields.io/badge/Clear-History-red?style=for-the-badge&logo=trash&logoColor=white)
![Safe](https://img.shields.io/badge/Safe-Operation-green?style=for-the-badge&logo=shield&logoColor=white)

**🧹 Multiple convenient ways to clear your clipboard history safely**

</div>

---

### 🎯 **Clear History Options**

| Method | Access Path | Best For |
|--------|-------------|----------|
| 🍎 **Menu Bar App** | View Clipboard History → 🗑️ Clear History | Quick access |
| 🕒 **Recent Items** | Recent Clipboard Items → 🗑️ Clear History | Direct access |
| 💻 **CLI Command** | `python3 cli_history_viewer.py clear` | Terminal users |
| 🔄 **Interactive CLI** | Type "clear" in interactive mode | CLI workflows |
| 🌐 **Web Viewer** | Click 🗑️ Clear History button | Browser interface |

---

### 🛡️ **Safety Features**

<table>
<tr>
<td align="center">

**🔒 Your data is protected with multiple safety measures**

</td>
</tr>
<tr>
<td>

- ✅ **Confirmation Dialogs**: All clear operations require user confirmation
- 📊 **Item Count Display**: Shows how many items will be cleared
- ⚠️ **Cannot Be Undone Warning**: Clear warning about irreversible action
- 🔄 **Automatic Menu Updates**: All interfaces refresh after clearing

</td>
</tr>
</table>

---

### 🎨 **User Experience**

| Feature | Icon | Description |
|---------|------|-------------|
| **Consistent Interface** | 🎯 | Same 🗑️ icon and behavior across all viewers |
| **Immediate Feedback** | 📢 | Success notifications and visual confirmation |
| **Error Handling** | 🛠️ | Graceful handling of file access issues |
| **Thread Safety** | 🧵 | Safe operation from any interface |

## 🔔 Enhanced Notifications

<div align="center">

![Notifications](https://img.shields.io/badge/Notifications-Enhanced-blue?style=for-the-badge&logo=bell&logoColor=white)
![Reliable](https://img.shields.io/badge/Reliable-System-green?style=for-the-badge&logo=check&logoColor=white)

**📢 Robust notification system with multiple fallback mechanisms**

</div>

---

### ✨ **Notification Features**

<table>
<tr>
<td width="50%">

#### 🍎 **Native Integration**
- 🔗 **AppleScript Integration**: Direct macOS notification access
- 🔄 **Dual System**: Primary AppleScript + fallback rumps
- 🔒 **Security Hardened**: Input sanitization prevents injection

</td>
<td width="50%">

#### 🎛️ **Customization**
- 🏷️ **Customizable Titles**: Configure through menu bar
- 🎯 **Context-Aware**: Different notifications for enhanced vs. polling
- 📊 **Status Updates**: Real-time feedback on all operations

</td>
</tr>
</table>

---

### 📋 **Notification Types**

| Type | Example | When Triggered |
|------|---------|----------------|
| 📋 **Clipboard Changes** | "Clipboard changed (enhanced)!" | Content detection |
| 🎛️ **Service Control** | "Service started successfully" | Start/stop/restart |
| ⏸️ **Pause/Resume** | "Monitoring paused" | State changes |
| 🧩 **Module Actions** | "Markdown converted to RTF" | Content processing |
| ⚙️ **Configuration** | "Settings updated" | Config changes |

---

### 🛡️ **Reliability Features**

<details>
<summary><b>🔧 Advanced Reliability Mechanisms</b></summary>

| Feature | Icon | Description |
|---------|------|-------------|
| **Timeout Protection** | ⏱️ | Prevents hanging on notification failures |
| **Error Logging** | 📝 | Failed notifications are logged for debugging |
| **Fallback Mechanisms** | 🔄 | Multiple notification methods ensure delivery |
| **Thread Safety** | 🧵 | Proper main thread handling for macOS |

</details>

## 📚 Quick Reference

<div align="center">

![Quick Reference](https://img.shields.io/badge/Quick-Reference-purple?style=for-the-badge&logo=book&logoColor=white)

**⚡ Essential commands and shortcuts for power users**

</div>

---

### 🎛️ **Service Management**

<details>
<summary><b>🔧 LaunchAgent Commands</b></summary>

```bash
# ▶️ Start the service
launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist

# ⏹️ Stop the service
launchctl unload ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist

# 🔄 Restart the service
launchctl unload ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist
launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist

# 📝 View logs
tail -f ~/Library/Logs/ClipboardMonitor.out.log
tail -f ~/Library/Logs/ClipboardMonitor.err.log
```

</details>

---

### 📦 **Dependencies**

<details>
<summary><b>🚀 Installation Commands</b></summary>

```bash
# 🎯 Run the installation script (recommended)
./install_dependencies.sh

# 🔧 Or install manually
python3 -m pip install --user -r requirements.txt
```

</details>

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

### History Viewer Issues
- **Blank Display**: Verify the history file exists at `~/Library/Application Support/ClipboardMonitor/clipboard_history.json`
- **GUI Viewer Not Opening**: Check if Tkinter is properly installed: `python3 -m tkinter`
- **Web Viewer Not Loading**: Ensure no other service is using port 8000, or try a different port
- **CLI Viewer Errors**: Verify the Rich library is installed: `pip3 list | grep rich`
- **History Not Updating**: Ensure the history module is enabled in configuration
- **Path Expansion Issues**: Check that the `utils.py` module is properly imported and `safe_expanduser` is being used

### Module Enable/Disable Issues
- **Module Still Processing When Disabled**: See [Module Enable/Disable Fix](MODULE_ENABLE_DISABLE_FIX.md) for configuration system fixes
- **Menu Bar Shows Wrong State**: Verify config.json module values are proper booleans or integers (0/false = disabled, true/1 = enabled)
- **Configuration Not Persisting**: Check that config.json is writable and not corrupted

## Shared Utilities

The application includes a shared utilities module (`utils.py`) that provides common functionality:

### Key Utilities
- **`show_notification(title, message)`**: Secure notification system with AppleScript injection prevention
- **`validate_string_input(value, name)`**: Input validation for all clipboard content
- **`safe_expanduser(path)`**: Secure tilde expansion with fallback mechanisms
- **`safe_subprocess_run(cmd, timeout=30)`**: Safe subprocess execution with timeout handling
- **`ContentTracker(max_history=10)`**: Content tracking to prevent processing loops
- **`ensure_directory_exists(path)`**: Safe directory creation with proper error handling

### Security Features
- **AppleScript Injection Prevention**: All notifications are sanitized to prevent code injection
- **Input Validation**: Comprehensive validation for all user inputs and clipboard content
- **Timeout Handling**: All subprocess operations include timeout protection
- **Path Safety**: Secure file path handling with proper expansion and validation

## Known Issues

### RTF Content History Tracking
- **Issue**: When Markdown is converted to RTF, the RTF content is correctly copied to the system clipboard and works when pasted into applications. However, the RTF content does not appear as an additional entry in this application's clipboard history viewers.
- **Impact**: Users can successfully use RTF content by pasting, but cannot see it in the application's history.
- **Workaround**: The original Markdown content remains visible in history, and RTF conversion works correctly for pasting purposes.
- **Status**: Under investigation - multiple attempts to resolve this clipboard monitoring limitation have not been successful.

## 🧪 Testing

<div align="center">

![Testing](https://img.shields.io/badge/Testing-Comprehensive-green?style=for-the-badge&logo=check&logoColor=white)
![Coverage](https://img.shields.io/badge/Coverage-90--95%25-brightgreen?style=for-the-badge&logo=shield&logoColor=white)

**🎯 Comprehensive test suite with 90-95% coverage across all functionality**

</div>

---

### 🚀 **Quick Start**

<details>
<summary><b>⚡ Essential Test Commands</b></summary>

```bash
# 🏃‍♂️ Run all tests
python3 tests/run_comprehensive_tests.py

# 🎯 Run specific test categories
python3 tests/test_clear_history_comprehensive.py
python3 tests/test_menu_bar_ui_comprehensive.py
python3 tests/test_performance_comprehensive.py
python3 tests/test_security_comprehensive.py
```

</details>

---

### 📋 **Test Categories**

| Category | Icon | Coverage | Description |
|----------|------|----------|-------------|
| **Clear History** | 🗑️ | ✅ Complete | Clear functionality across all interfaces |
| **Menu Bar UI** | 🍎 | ✅ Complete | Menu interactions and state changes |
| **End-to-End Workflows** | 🔄 | ✅ Complete | Complete user scenarios |
| **Error Handling** | 🛠️ | ✅ Complete | Edge cases and failure conditions |
| **Performance** | ⚡ | ✅ Complete | Large datasets and resource usage |
| **Real-time Monitoring** | 📊 | ✅ Complete | Clipboard change detection |
| **Configuration** | ⚙️ | ✅ Complete | Settings validation and error handling |
| **Security** | 🔒 | ✅ Complete | Input validation and injection prevention |

---

### 📚 **Test Documentation**

| Guide | Icon | Purpose |
|-------|------|---------|
| **[Testing Quick Start](TESTING_QUICK_START.md)** | ⚡ | Quick reference for developers |
| **[Complete Testing Guide](TESTING.md)** | 📖 | Comprehensive testing documentation |
| **[Test Suite Details](COMPREHENSIVE_TEST_SUITE.md)** | 🔍 | Detailed test descriptions and coverage |

---

### 📦 **Prerequisites**

```bash
# 🔧 Optional: For performance tests
pip install psutil
```

## Creating Custom Modules

See the [Module Development Guide](MODULE_DEVELOPMENT.md) for information on creating your own processing modules.

For information about module configuration and enable/disable functionality, see the [Module Enable/Disable Fix](MODULE_ENABLE_DISABLE_FIX.md) documentation.

---

## 🚨 Logging Format Update (June 2025)

- **All logging is now plain text**: No colorized or Rich formatting is used anywhere in the application.
- **Enhanced log format**: All logs include timestamps, padded log levels, section separators, and multi-line support for better readability.
- **Log file separation**: Output and error logs are now strictly separated for clarity.
- **Consistent logging**: All logging uses `log_event` and `log_error` helpers for a uniform format across all modules and utilities.
- **All configuration options**: Every option in `config.json` is now settable from the Preferences menu in the menu bar app.
- **No logging for update_recent_history_menu**: All logging related to this function has been removed as per user request.

## 📝 Logging

- **All logs are now written to:**
  - `~/Library/Logs/ClipboardMonitor.out.log` (output/info)
  - `~/Library/Logs/ClipboardMonitor.err.log` (errors/warnings)
- **Log format:** Plain text, with timestamps, padded log levels, section separators, and multi-line support. No color or Rich formatting is used.
- **Log file locations are unified** and match the LaunchAgent plist configuration. The config file does not control log file paths.

**To view logs:**
```bash
tail -f ~/Library/Logs/ClipboardMonitor.out.log
```

**To clear logs:**
```bash
truncate -s 0 ~/Library/Logs/ClipboardMonitor.out.log ~/Library/Logs/ClipboardMonitor.err.log
```

## 📄 License

<div align="center">

![MIT License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge&logo=opensourceinitiative&logoColor=white)

**This project is licensed under the MIT License - see the LICENSE file for details.**

</div>

---

<div align="center">

### 🎉 **Thank you for using Clipboard Monitor!**

![Made with Love](https://img.shields.io/badge/Made_with-❤️-red?style=for-the-badge)
![macOS](https://img.shields.io/badge/Built_for-macOS-blue?style=for-the-badge&logo=apple&logoColor=white)
![Python](https://img.shields.io/badge/Powered_by-Python-yellow?style=for-the-badge&logo=python&logoColor=white)

**🚀 Star this repo if you find it useful! ⭐**

</div>
