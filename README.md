# 📋 Clipboard Monitor

A powerful, modular clipboard monitoring and processing application for macOS with advanced memory monitoring and a clean, user-focused interface.

## 🚀 Quick Installation

**Super Simple - One Click Installation:**

1. Download `ClipboardMonitor-1.0.pkg`
2. Double-click the PKG file
3. Follow installer prompts (Continue → Install → Enter Password)
4. Done! App automatically starts in your menu bar

## ✨ Key Features

### 📝 **Modular Processing System**
- **Markdown Processor** - Automatic markdown formatting and processing
- **Mermaid Diagrams** - Generate, copy, and view diagram code with theme support
- **Draw.io Integration** - Seamless diagram workflow with advanced URL parameters
- **Code Formatter** - Intelligent code formatting and processing
- **Clipboard History** - Track, view, and manage clipboard items with browser/terminal integration

### 🧠 **Advanced Memory Monitoring**
- Real-time memory usage visualization
- Interactive dashboard with beautiful charts and graphs
- Memory leak detection and analysis
- Performance optimization tools
- Historical usage tracking

### 🎯 **Clean, Modular Interface**
- **Invisible Disabled Modules** - Only see features you actually use
- **Module Discovery** - Easy enable/disable via "Add Modules" in settings
- **Contextual Organization** - Related functionality grouped together
- **Zero Clutter** - Cleanest possible interface design

## 🔧 Architecture

### **Modular Design Philosophy**
Each module can be independently enabled/disabled:
- Disabled modules are completely invisible (zero clutter)
- Enabled modules show full functionality and settings
- Module discovery available via Settings → Add Modules
- Dynamic menu rebuilding when modules are toggled

### **Professional Distribution**
- Native macOS PKG installer
- Automatic LaunchAgent configuration
- System-level service integration
- Professional installation experience
- One-click uninstallation support

## 📊 Menu Structure

```
📊 Status: Running (Enhanced)
🧠 Memory Usage Visualization
---
⏸️ Pause/Resume Monitoring
🔄 Service Control
---
📚 Clipboard History (if enabled)
📝 Markdown (if enabled)  
🧩 Mermaid (if enabled)
🎨 Draw.io (if enabled)
---
🧠 Memory Monitor & Dashboard
⚙️ Settings
   ├── ➕ Add Modules (discover disabled modules)
   ├── Module-specific settings
   └── System configuration
---
📋 Logs & Diagnostics
❌ Quit
```

## 🛠️ Development

### **Build System**
```bash
# Build and create PKG installer
./build_create_install_pkg.sh

# Test PKG functionality  
./test_pkg_install.sh

# Development with VS Code
# Use bottom toolbar buttons for quick actions
```

### **VS Code Integration**
Professional development environment with task buttons:
- 📦 Build PKG - Create installer package
- 🧪 Test PKG - Validate installer functionality
- 🚀 Build Create Install DMG - Legacy DMG support
- 🔄 Service Management - Start/stop/restart services
- 📊 Dashboard - Launch memory monitoring dashboard

## 📚 Documentation

- **[PKG Migration Journey](docs/PKG-Migration-Journey.md)** - Complete development story
- **[Memory Optimization](docs/Memory%20Optimization/)** - Performance guides
- **[Module Development](docs/MODULE_DEVELOPMENT.md)** - Creating new modules
- **[Testing Guide](docs/TESTING.md)** - Comprehensive testing documentation

## 🔧 Troubleshooting

### **Installation Issues**
- Ensure admin privileges for PKG installation
- Allow system integration when prompted
- Check System Preferences → Security if blocked

### **Missing Features**
- Use "⚙️ Settings → ➕ Add Modules" to enable disabled modules
- Restart services via menu bar if needed
- Check logs via "📋 Logs" menu for diagnostics

### **Memory Issues**
- Use built-in memory dashboard for analysis
- Enable memory monitoring via menu bar
- Check "🧠 Memory Monitor" for real-time stats

## 📞 Support

- **GitHub**: [Clipboard-Monitor Repository](https://github.com/omairaslam/Clipboard-Monitor)
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Documentation**: Comprehensive guides in `docs/` folder
- **Version**: 1.0.0 (Professional PKG Distribution)

## 🏗️ Technical Details

- **Platform**: macOS (native PKG installer)
- **Architecture**: Modular Python application with PyInstaller bundling
- **Services**: Automatic LaunchAgent configuration
- **Memory**: Advanced monitoring with leak detection
- **Interface**: Native macOS menu bar integration
- **Distribution**: Professional PKG installer with system integration

---

**Built with ❤️ for macOS users who want powerful, clean, and modular clipboard processing.**
