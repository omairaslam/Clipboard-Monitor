# 🚀 Clipboard Monitor - Quick Installation Guide

## One-Click Installation (Recommended)

### Step 1: Download
Download `ClipboardMonitor-1.0.pkg` from the releases page.

### Step 2: Install
1. **Double-click** `ClipboardMonitor-1.0.pkg`
2. **Click "Continue"** through the installer screens
3. **Click "Install"** when prompted
4. **Enter your password** for system-level installation
5. **Click "Close"** when installation completes

### Step 3: Verify
- Look for the Clipboard Monitor icon in your menu bar (top-right)
- The app starts automatically after installation
- If you don't see it, wait 10-15 seconds for services to start

## ✅ What Gets Installed

- **Application**: Installed to `/Applications/` (if needed)
- **Services**: Automatically configured and started
- **Menu Bar App**: Appears in your menu bar
- **Background Processing**: Runs automatically

## 🎯 First Use

1. **Click the menu bar icon** to see available features
2. **Enable modules** you want via "⚙️ Settings → ➕ Add Modules"
3. **Configure settings** for each enabled module
4. **Start using** clipboard processing features!

## 🔧 Available Modules

**Enable only what you need for a clean interface:**

- **📚 Clipboard History** - Track and manage clipboard items
- **📝 Markdown Processor** - Automatic markdown formatting  
- **🧩 Mermaid Diagrams** - Generate and view diagram code
- **🎨 Draw.io Integration** - Seamless diagram workflow
- **🔧 Code Formatter** - Intelligent code processing

## ❓ Troubleshooting

### Installation Issues
- **"Cannot be opened"**: Right-click → Open, then click "Open" again
- **Permission denied**: Ensure you have admin privileges
- **Installer blocked**: Check System Preferences → Security & Privacy

### App Not Appearing
- **Wait 15 seconds** for services to start
- **Check Activity Monitor** for "ClipboardMonitor" processes
- **Restart services** via Terminal: `launchctl load ~/Library/LaunchAgents/com.clipboardmonitor*.plist`

### Menu Bar Missing
- **Enable modules** via "⚙️ Settings → ➕ Add Modules"
- **Restart app** via menu bar if visible
- **Check logs** for errors (see menu bar → Logs)

## 🗑️ Uninstallation

To completely remove Clipboard Monitor:

```bash
# Stop services
launchctl unload ~/Library/LaunchAgents/com.clipboardmonitor*.plist

# Remove files
sudo pkgutil --forget com.clipboardmonitor.pkg
rm -rf /Applications/ClipboardMonitor.app
rm ~/Library/LaunchAgents/com.clipboardmonitor*.plist
```

## 📞 Need Help?

- **GitHub Issues**: [Report problems](https://github.com/omairaslam/Clipboard-Monitor/issues)
- **Documentation**: See `docs/` folder for detailed guides
- **Logs**: Check menu bar → "📋 Logs" for diagnostic information

---

**Installation typically takes 30 seconds and requires no manual configuration!**
