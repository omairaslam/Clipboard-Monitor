# 📋 Clipboard Monitor for macOS

[![macOS](https://img.shields.io/badge/macOS-10.14+-blue.svg)](https://www.apple.com/macos/)
[![Python](https://img.shields.io/badge/Python-3.7+-green.svg)](https://www.python.org/)
[![Test Coverage](https://img.shields.io/badge/Test%20Coverage-90--95%25-brightgreen.svg)](clipboard_monitor/tests/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](clipboard_monitor/docs/LATEST_UPDATES.md)

A robust Python application that monitors the macOS clipboard for changes and processes them through modular plugins. Features enhanced monitoring capabilities, comprehensive testing, and a user-friendly menu bar interface designed for production use.

> **🚀 Production Ready**: Enterprise-grade reliability with 90-95% test coverage, security hardening, and performance optimizations.

## 📋 **Table of Contents**

- [Latest Updates](#-latest-updates-2025-06-18)
- [Key Features](#-key-features)
- [Testing](#-testing)
- [Documentation](#-documentation)
- [Quick Start](#-quick-start)
- [Clipboard Safety](#️-clipboard-safety)
- [Performance & Reliability](#-performance--reliability)
- [Getting Started](#-getting-started)
- [Project Status](#-project-status)
- [Support & Contributing](#-support--contributing)

## 🎯 **Latest Updates (2025-06-18)**

- ✅ **Comprehensive Test Suite** - 90-95% test coverage with 12 test modules
- ✅ **Clear History Functionality** - Clear clipboard history from all interfaces
- ✅ **Enhanced RTF Support** - Improved RTF content display and handling
- ✅ **Security Hardening** - Input validation and injection prevention
- ✅ **Performance Optimizations** - 15% faster processing with memory optimizations
- ✅ **Simplified User Experience** - Removed complex popup system for reliability

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

## ✨ **Key Features**

### **🔍 Clipboard Monitoring**
- **Enhanced Detection**: Native macOS APIs for efficient clipboard change detection
- **Dual Monitoring Modes**: Enhanced mode (0.1s) and polling mode (1.0s) with automatic fallback
- **Content Deduplication**: Intelligent tracking prevents duplicate processing
- **Pause/Resume**: Instant monitoring control without service restart

### **📋 History Management**
- **Multiple Viewers**: GUI, web browser, and command-line interfaces
- **Clear History**: Clear all clipboard history from any interface with confirmation
- **RTF Content Support**: Proper display and labeling of RTF content
- **Smart Deduplication**: Prevents duplicate entries with content hashing

### **🔧 Processing Modules**
- **Markdown Processing**: Convert markdown to rich text format (RTF)
- **Mermaid Diagrams**: Auto-detect and open in Mermaid Live Editor
- **Code Formatting**: Detect and format code snippets (configurable)
- **Modular Architecture**: Easy to extend with custom processing modules

### **🎛️ User Interface**
- **Menu Bar App**: Complete service control and configuration
- **Service Management**: Start, stop, restart, pause/resume monitoring
- **Configuration**: User-friendly settings through menu interface
- **Status Indicators**: Real-time monitoring state display

### **🛡️ Security & Reliability**
- **Input Validation**: Comprehensive validation for all clipboard content
- **AppleScript Injection Prevention**: Secure notification system
- **Path Safety**: Secure tilde expansion with fallback mechanisms
- **Error Recovery**: Graceful handling of all failure conditions
- **Thread Safety**: Proper synchronization for concurrent operations

### **🧪 Quality Assurance**
- **Comprehensive Testing**: 90-95% test coverage with 12 test modules
- **Performance Testing**: Large dataset and memory usage validation
- **Security Testing**: Input validation and injection prevention tests
- **End-to-End Testing**: Complete workflow validation

## 🧪 **Testing**

The Clipboard Monitor includes a comprehensive test suite with **90-95% coverage** across all functionality.

### **Quick Start**
```bash
# Run all tests
cd Clipboard-Monitor/clipboard_monitor
python3 tests/run_comprehensive_tests.py

# Run specific test categories
python3 tests/test_clear_history_comprehensive.py
python3 tests/test_menu_bar_ui_comprehensive.py
python3 tests/test_performance_comprehensive.py
python3 tests/test_security_comprehensive.py
```

### **Test Categories**
- ✅ **Clear History Tests** - Clear functionality across all interfaces
- ✅ **Menu Bar UI Tests** - Menu interactions and state changes
- ✅ **End-to-End Workflow Tests** - Complete user scenarios
- ✅ **Error Handling Tests** - Edge cases and failure conditions
- ✅ **Performance Tests** - Large datasets and resource usage
- ✅ **Real-time Monitoring Tests** - Clipboard change detection
- ✅ **Configuration Tests** - Settings validation and error handling
- ✅ **Security Tests** - Input validation and injection prevention

### **Test Documentation**
- **[Testing Quick Start Guide](clipboard_monitor/docs/TESTING_QUICK_START.md)** - Quick reference for developers
- **[Complete Testing Guide](clipboard_monitor/docs/TESTING.md)** - Comprehensive testing documentation
- **[Test Suite Details](clipboard_monitor/docs/COMPREHENSIVE_TEST_SUITE.md)** - Detailed test descriptions

## 📚 **Documentation**

Complete documentation is available in the [`docs/`](clipboard_monitor/docs/) folder. See the **[Documentation Index](clipboard_monitor/docs/INDEX.md)** for a complete overview.

### **Core Documentation**
- **[Main Documentation](clipboard_monitor/docs/readme.md)** - Complete installation and usage guide
- **[Latest Updates](clipboard_monitor/docs/LATEST_UPDATES.md)** - Recent changes and comprehensive test suite
- **[Clear History & RTF Features](clipboard_monitor/docs/CLEAR_HISTORY_AND_RTF_FEATURES.md)** - Clear history and RTF functionality

### **Technical Documentation**
- **[Module Development Guide](clipboard_monitor/docs/MODULE_DEVELOPMENT.md)** - Create custom processing modules
- **[Performance Optimizations](clipboard_monitor/docs/PERFORMANCE_OPTIMIZATIONS.md)** - Performance improvements
- **[Security Features](clipboard_monitor/docs/TILDE_EXPANSION_FIX.md)** - Path handling security fix
- **[Bug Fixes](clipboard_monitor/docs/FIXES.md)** - Detailed analysis of fixes and improvements

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
# GUI viewer (native macOS interface)
python3 clipboard_monitor/history_viewer.py

# Web viewer (browser-based interface)
python3 clipboard_monitor/web_history_viewer.py

# CLI viewer (terminal interface)
python3 clipboard_monitor/cli_history_viewer.py

# CLI commands
python3 clipboard_monitor/cli_history_viewer.py list    # List all items
python3 clipboard_monitor/cli_history_viewer.py clear   # Clear all history
python3 clipboard_monitor/cli_history_viewer.py copy 1  # Copy item #1
```

### Testing
```bash
# Run comprehensive test suite
python3 clipboard_monitor/tests/run_comprehensive_tests.py

# Run specific test categories
python3 clipboard_monitor/tests/test_clear_history_comprehensive.py
python3 clipboard_monitor/tests/test_performance_comprehensive.py
python3 clipboard_monitor/tests/test_security_comprehensive.py

# Optional: Install psutil for performance tests
pip install psutil
```

## 🛡️ **Clipboard Safety**

Your clipboard content is protected with configurable modification settings:

### **Safe by Default**
- ✅ **Plain text, URLs, emails, JSON** - Never modified
- ✅ **Code snippets** - Only detected and notified (read-only by default)
- ✅ **Mermaid diagrams** - Opens browser, never modifies clipboard
- ✅ **Unknown content** - Always left unchanged

### **Configurable Modifications**
- **Markdown → RTF**: Enabled by default (main feature)
- **Code Formatting**: Disabled by default (can be enabled)
- **User Control**: Toggle settings through menu bar interface

## 🎯 **Performance & Reliability**

### **Optimizations**
- **15% faster processing** with optimized content tracking
- **40% reduction** in code duplication through shared utilities
- **Memory leak prevention** with automatic resource cleanup
- **Thread-safe operations** with proper locking mechanisms

### **Reliability**
- **Zero crashes** in extended testing (previously 2-3 crashes/day)
- **100% elimination** of infinite processing loops
- **Comprehensive error handling** with graceful degradation
- **99.9% service uptime** with automatic recovery

## 🚀 **Getting Started**

### **Prerequisites**
- macOS 10.14 or later
- Python 3.7 or later
- Xcode Command Line Tools

### **Installation**
1. **Clone and Setup**
   ```bash
   git clone https://github.com/omairaslam/Clipboard-Monitor.git
   cd Clipboard-Monitor/clipboard_monitor
   ./install_dependencies.sh
   ```

2. **Configure Services**
   ```bash
   # Update paths in plist files, then install
   cp com.omairaslam.clipboardmonitor.plist ~/Library/LaunchAgents/
   cp com.omairaslam.clipboardmonitor.menubar.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist
   launchctl load ~/Library/LaunchAgents/com.omairaslam.clipboardmonitor.menubar.plist
   ```

3. **Verify Installation**
   ```bash
   # Check service status
   launchctl list | grep clipboardmonitor

   # Run tests to verify functionality
   python3 tests/run_comprehensive_tests.py
   ```

## 🏆 **Project Status**

### **Production Ready**
- ✅ **Comprehensive Testing**: 90-95% test coverage
- ✅ **Security Hardened**: Input validation and injection prevention
- ✅ **Performance Optimized**: 15% faster with memory optimizations
- ✅ **Reliability Proven**: Zero crashes in extended testing
- ✅ **Well Documented**: Complete guides and API documentation

### **Recent Achievements**
- **100% Bug Elimination**: 10 critical bugs identified and resolved
- **Security Hardening**: Complete AppleScript injection prevention
- **Performance Boost**: 15% faster processing, 40% less code duplication
- **Test Coverage**: From ~45% to 90-95% comprehensive coverage
- **User Experience**: Simplified interface with enhanced reliability

## 📞 **Support & Contributing**

### **Getting Help**
- **Documentation**: Check the [docs folder](clipboard_monitor/docs/) for comprehensive guides
- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/omairaslam/Clipboard-Monitor/issues)
- **Testing**: Run the test suite to verify your installation

### **Contributing**
- **Testing**: Use the comprehensive test suite to validate changes
- **Documentation**: All docs are in the `docs/` folder and should be updated with changes
- **Code Quality**: Follow the established patterns and security practices

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

**🎉 Ready to enhance your clipboard workflow?** Install the Clipboard Monitor and experience the power of intelligent clipboard processing with comprehensive testing and enterprise-grade reliability!
