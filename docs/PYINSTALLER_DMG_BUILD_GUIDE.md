# PyInstaller DMG Build Guide

## Overview

This document describes the complete PyInstaller-based build system for creating a self-contained DMG distribution of Clipboard Monitor. This approach creates a fully standalone application that doesn't require any Python installation on the user's machine.

## Build System Components

### 1. PyInstaller Spec Files

#### `main.spec`
- **Purpose**: Builds the background clipboard monitoring service
- **Output**: `ClipboardMonitor` executable
- **Key Features**:
  - Includes all Python modules and dependencies
  - Bundles configuration files and templates
  - Creates standalone executable with embedded Python interpreter

#### `menu_bar_app.spec`
- **Purpose**: Builds the menu bar interface application
- **Output**: `ClipboardMonitorMenuBar` executable  
- **Key Features**:
  - Includes rumps framework for menu bar functionality
  - Bundles all UI-related dependencies
  - Includes memory monitoring and dashboard components

### 2. Build Scripts

#### `build_pyinstaller.sh`
- **Purpose**: Orchestrates the complete build process
- **Features**:
  - Installs PyInstaller and dependencies automatically
  - Builds both executables using spec files
  - Creates unified app bundle structure
  - Updates plist templates for bundled executables
  - Provides detailed build feedback

#### `create_dmg.sh`
- **Purpose**: Creates professional DMG for distribution
- **Features**:
  - Creates properly formatted DMG with Applications symlink
  - Includes README and installation scripts
  - Sets up DMG window appearance and layout
  - Handles code signing (if certificates available)
  - Verifies DMG integrity

### 3. App Bundle Structure

```
Clipboard Monitor.app/
├── Contents/
│   ├── Info.plist                    # App bundle metadata
│   ├── MacOS/
│   │   └── ClipboardMonitorMenuBar   # Main executable (menu bar app)
│   └── Resources/
│       ├── Services/
│       │   └── ClipboardMonitor      # Background service executable
│       ├── *.py                      # Python source files as resources
│       ├── modules/                  # Module directory
│       ├── config.json               # Configuration file
│       └── *.plist.template          # LaunchAgent templates
```

## Build Process

### Prerequisites
- macOS 10.14 or later
- Python 3.9 or later
- Git (for cloning repository)

### Step 1: Prepare Environment
```bash
git clone https://github.com/omairaslam/Clipboard-Monitor.git
cd Clipboard-Monitor
```

### Step 2: Build Application
```bash
./build_pyinstaller.sh
```

This script will:
1. Install PyInstaller and all dependencies
2. Build both executables
3. Create unified app bundle
4. Update configuration templates

### Step 3: Create DMG
```bash
./create_dmg.sh
```

This script will:
1. Create temporary DMG
2. Copy app bundle and additional files
3. Set up DMG appearance
4. Create compressed, distributable DMG

## Key Improvements Over py2app

### 1. True Self-Containment
- **PyInstaller**: Embeds complete Python interpreter and all dependencies
- **py2app**: Relies on system Python frameworks

### 2. Better Dependency Handling
- **PyInstaller**: Automatically detects and includes hidden imports
- **py2app**: Often requires manual specification of dependencies

### 3. Cross-Platform Compatibility
- **PyInstaller**: Works across different macOS versions
- **py2app**: More sensitive to macOS version differences

### 4. Smaller Bundle Size
- **PyInstaller**: Only includes necessary components
- **py2app**: Often includes entire framework directories

## Installation Process

### For End Users
1. Download and open `ClipboardMonitor-1.0.dmg`
2. Drag `Clipboard Monitor.app` to Applications folder
3. Launch the app (menu bar icon will appear)
4. Run the included `install.sh` script to set up background services

### Service Configuration
The installation script automatically:
- Creates LaunchAgent plist files pointing to bundled executables
- Sets up proper working directories and log paths
- Loads and starts both services
- Provides detailed status feedback

## Technical Details

### Dependencies Included
- **Core**: pyperclip, rumps, psutil
- **macOS Frameworks**: Complete PyObjC framework suite
- **Standard Library**: All required Python standard library modules

### Hidden Imports Handled
- Dynamic module loading from `modules/` directory
- PyObjC framework components
- Web server components for dashboard functionality
- Memory monitoring and profiling tools

### Resource Files
- Configuration templates
- Python source files (for subprocess calls)
- Module directory with all processing modules
- LaunchAgent plist templates

## Troubleshooting

### Build Issues
- **PyObjC Installation**: Use `pip3 install pyobjc` for complete framework
- **Permission Errors**: Ensure build scripts are executable (`chmod +x`)
- **Missing Dependencies**: Run `pip3 install -r requirements.txt`

### Runtime Issues
- **Service Not Starting**: Check log files in `~/Library/Logs/`
- **Menu Bar Not Appearing**: Verify app has accessibility permissions
- **Module Loading Errors**: Ensure all Python files are in Resources directory

## File Locations

### Build Artifacts
- `Clipboard Monitor.app` - Final app bundle
- `ClipboardMonitor-1.0.dmg` - Distributable DMG
- `build_pyinstaller/` - Build cache (can be deleted)
- `dist_pyinstaller/` - Individual app bundles (can be deleted)

### Runtime Files
- `~/Library/LaunchAgents/com.clipboardmonitor*.plist` - Service definitions
- `~/Library/Logs/ClipboardMonitor*.log` - Service logs
- `~/.clipboard_monitor/` - User data and configuration

## Distribution

The final `ClipboardMonitor-1.0.dmg` file is completely self-contained and can be distributed to users without any additional requirements. Users simply need to:

1. Download the DMG
2. Install the app
3. Run the setup script

No Python installation or additional dependencies are required on the target machine.
