# Copy Code Feature Documentation - Clipboard Monitor

## 📋 Overview

This document provides comprehensive documentation for the new **Copy Code** configuration options added to the Mermaid and Draw.io modules in Clipboard Monitor. This feature gives users granular control over clipboard operations with sequential copying behavior.

## ✨ New Features

### **Copy Code Configuration Options**
- **Mermaid Module**: `mermaid_copy_code` - Controls copying of original Mermaid diagram code
- **Draw.io Module**: `drawio_copy_code` - Controls copying of original Draw.io XML content

### **Sequential Clipboard Operations**
When both "Copy Code" and "Copy URL" are enabled, the system performs operations in this order:
1. **First**: Original code/XML is copied to clipboard with notification
2. **Second**: Generated URL is copied to clipboard with notification
3. **Third**: Browser opens (if "Open in Browser" is enabled)

### **Independent Control**
Each feature can be enabled/disabled independently:
- Copy Code only
- Copy URL only  
- Open Browser only
- Any combination of the above

## 🎛️ Menu Interface

### **Mermaid Settings Menu**
```
📋 Menu Bar → Preferences → Module Settings → Mermaid Settings
├── Copy Code (✅ Default: Enabled)
├── Copy URL (❌ Default: Disabled)
├── Open in Browser (✅ Default: Enabled)
└── Editor Theme (Submenu: Default/Dark/Forest/Neutral)
```

### **Draw.io Settings Menu**
```
📋 Menu Bar → Preferences → Module Settings → Draw.io Settings
├── Copy Code (✅ Default: Enabled)
├── Copy URL (✅ Default: Enabled)
├── Open in Browser (✅ Default: Enabled)
└── URL Parameters (Submenu with various options)
```

## ⚙️ Configuration

### **JSON Configuration**
```json
{
  "modules": {
    "mermaid_copy_code": true,    // Copy original Mermaid code
    "mermaid_copy_url": false,    // Copy generated URL
    "mermaid_open_in_browser": true,  // Open browser
    "drawio_copy_code": true,     // Copy original XML
    "drawio_copy_url": true,      // Copy generated URL
    "drawio_open_in_browser": true    // Open browser
  }
}
```

### **Default Values**
| Module | Copy Code | Copy URL | Open Browser |
|--------|-----------|----------|--------------|
| **Mermaid** | ✅ `true` | ❌ `false` | ✅ `true` |
| **Draw.io** | ✅ `true` | ✅ `true` | ✅ `true` |

## 🔄 Behavior Examples

### **Mermaid Module Scenarios**

#### Scenario 1: Copy Code Only (Default)
- **Config**: `copy_code: true, copy_url: false, open_browser: true`
- **Result**: Original Mermaid code stays in clipboard, browser opens

#### Scenario 2: Copy Both Code and URL
- **Config**: `copy_code: true, copy_url: true, open_browser: true`
- **Result**: 
  1. Mermaid code copied → notification
  2. URL copied → notification  
  3. Browser opens

#### Scenario 3: URL Only
- **Config**: `copy_code: false, copy_url: true, open_browser: false`
- **Result**: Only URL copied to clipboard

### **Draw.io Module Scenarios**

#### Scenario 1: Copy Both (Default)
- **Config**: `copy_code: true, copy_url: true, open_browser: true`
- **Result**:
  1. XML copied → notification
  2. URL copied → notification
  3. Browser opens

#### Scenario 2: XML Only
- **Config**: `copy_code: true, copy_url: false, open_browser: false`
- **Result**: Original XML stays in clipboard

## 🔔 Notifications

### **Notification Types**
- **"Mermaid Code"**: "Diagram code copied to clipboard"
- **"Mermaid URL"**: "URL copied to clipboard"  
- **"Draw.io XML"**: "XML code copied to clipboard"
- **"Draw.io URL"**: "URL copied to clipboard"
- **"Browser"**: "Opened in browser"

### **Sequential Notifications**
When both code and URL copying are enabled, users receive separate notifications for each operation, providing clear feedback about what was copied.

## 🛠️ Technical Implementation

### **Module Changes**
- **Enhanced clipboard handling** with sequential operations
- **Improved notification system** with operation-specific messages
- **Configuration-driven behavior** with fallback defaults
- **Backward compatibility** maintained

### **Menu Bar Integration**
- **New menu items** added to existing settings menus
- **Updated callback functions** to handle new configuration keys
- **Consistent menu ordering** across modules

## 📚 Documentation Updates

### **Files Updated**
- `docs/readme.md` - Main documentation with feature descriptions
- `docs/LATEST_UPDATES.md` - Added Copy Code feature section
- `docs/INDEX.md` - Updated feature references
- `docs/MODULE_DEVELOPMENT.md` - Added sequential operations pattern
- `docs/MENU_ORGANIZATION.md` - Updated menu structure
- `docs/COPY_CODE_FEATURE_DOCUMENTATION.md` - This comprehensive guide

### **Configuration Schema**
- Updated JSON schema examples in all documentation
- Added new configuration keys with proper defaults
- Maintained backward compatibility notes

## 🎯 User Benefits

### **Enhanced Control**
- **Granular clipboard management** - choose exactly what gets copied
- **Logical operation sequence** - code first, then URL, then browser
- **Independent feature control** - enable/disable each feature separately

### **Improved Workflow**
- **Preserve original content** when needed
- **Quick access to generated URLs** when required
- **Flexible browser opening** based on user preference

### **Clear Feedback**
- **Separate notifications** for each clipboard operation
- **Immediate confirmation** of what was copied
- **Transparent operation sequence**

## 🔧 Migration Notes

### **Existing Users**
- **No breaking changes** - all existing functionality preserved
- **New defaults applied** - Copy Code enabled by default
- **Menu items added** - new options appear in existing menus

### **Configuration Migration**
- **Automatic defaults** - new keys get default values if missing
- **Backward compatibility** - old configurations continue to work
- **Service restart** - required for menu changes to take effect

## 📝 Future Enhancements

### **Potential Improvements**
- **Custom notification messages** - user-configurable notification text
- **Clipboard history integration** - track sequential operations
- **Timing controls** - configurable delays between operations
- **Export/import settings** - share configurations between installations

This feature significantly enhances the user experience by providing complete control over clipboard operations while maintaining the simplicity and reliability of the existing system.
