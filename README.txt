📋 CLIPBOARD MONITOR - INSTALLATION GUIDE
==========================================

🚀 QUICK INSTALLATION (Recommended):
1. Double-click "install.sh" for automated installation
2. The script will open this DMG in list view for easy access
3. Drag both .plist files onto the "LaunchAgents" symlink
4. The app will be copied automatically and appear in your menu bar

📁 WHAT'S INCLUDED:
• Clipboard Monitor.app - Main application
• install.sh - Automated installation script  
• uninstall.sh - Complete removal script
• LaunchAgents/ - System service configuration folder
• *.plist files - Background service definitions

⚙️ MANUAL INSTALLATION (Advanced):
If automated installation doesn't work:
1. Drag .plist files onto LaunchAgents symlink (or copy to ~/Library/LaunchAgents/)
2. Manually copy app to Applications folder if needed
3. Load services: launchctl load ~/Library/LaunchAgents/com.clipboardmonitor*.plist

💡 AUTOMATED INSTALLATION:
The install.sh script now automatically copies the app to Applications!
Just drag the .plist files to the LaunchAgents symlink and run the script.

💡 LIST VIEW ADVANTAGE:
The DMG opens in list view showing all files clearly with the LaunchAgents
symlink visible - just drag both .plist files onto it for instant installation!

🔧 FEATURES:
• Real-time clipboard monitoring
• Memory usage tracking and optimization
• Menu bar integration with quick access
• Advanced monitoring dashboard
• Automatic background service management

❓ TROUBLESHOOTING:
• If multiple instances spawn: Run uninstall.sh then reinstall
• For permission issues: Check System Preferences > Security
• Memory issues: Use built-in memory monitor in menu bar

📞 SUPPORT:
GitHub: https://github.com/omairaslam/Clipboard-Monitor
Version: 1.0.0

🗑️ UNINSTALLATION:
Run uninstall.sh to completely remove all components
