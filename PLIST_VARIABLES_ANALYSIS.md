# 📋 PLIST Variables Analysis - Simplified 2-Variable Approach

## 🔧 **The 2 PLIST_ Variables in `_config.sh` (UPDATED)**

```bash
# --- Service Configuration ---
PLIST_BACKGROUND="com.clipboardmonitor.service.dev.plist"      # Plist filename
PLIST_MENUBAR="com.clipboardmonitor.menubar.dev.plist"         # Plist filename

# Note: Service labels for launchctl list are derived from filenames by removing .plist extension
# Use ${PLIST_BACKGROUND%.plist} and ${PLIST_MENUBAR%.plist} when labels are needed
```

---

## 📁 **1. PLIST_BACKGROUND** 
**Purpose:** Filename of the main background service plist file  
**Value:** `"com.clipboardmonitor.service.dev.plist"`

### **Used In:**
| Script | Line | Usage | Purpose |
|--------|------|-------|---------|
| `start_services.sh` | 12 | `launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"` | Load main service |
| `stop_services.sh` | 14 | `launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"` | Stop main service |
| `restart_services.sh` | 20,22 | `launchctl unload/load "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"` | Restart main service |
| `restart_main.sh` | 10,12 | `launchctl unload/load "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"` | Restart main service only |

### **What It Controls:**
- **Main Clipboard Monitor Service** (main.py)
- **Background clipboard monitoring**
- **Module processing** (Mermaid, Draw.io, etc.)
- **File:** `~/Library/LaunchAgents/com.clipboardmonitor.service.dev.plist`

---

## 📱 **2. PLIST_MENUBAR**
**Purpose:** Filename of the menu bar app plist file  
**Value:** `"com.clipboardmonitor.menubar.dev.plist"`

### **Used In:**
| Script | Line | Usage | Purpose |
|--------|------|-------|---------|
| `start_services.sh` | 17 | `launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR"` | Load menu bar app |
| `stop_services.sh` | 19 | `launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR"` | Stop menu bar app |
| `restart_services.sh` | 31,33 | `launchctl unload/load "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR"` | Restart menu bar app |
| `restart_menubar.sh` | 10,12 | `launchctl unload/load "$LAUNCH_AGENTS_DIR/$PLIST_MENUBAR"` | Restart menu bar only |

### **What It Controls:**
- **Menu Bar Application** (menu_bar_app.py)
- **System tray icon** (📋)
- **User interface menus**
- **Configuration settings**
- **File:** `~/Library/LaunchAgents/com.clipboardmonitor.menubar.dev.plist`

---

## 🎯 **How Labels Are Derived (NEW APPROACH)**

Instead of separate label variables, labels are now **derived dynamically** using bash parameter expansion:

```bash
# Derive labels when needed:
BACKGROUND_LABEL="${PLIST_BACKGROUND%.plist}"    # = "com.clipboardmonitor.service.dev"
MENUBAR_LABEL="${PLIST_MENUBAR%.plist}"          # = "com.clipboardmonitor.menubar.dev"
```

### **Usage Examples:**
```bash
# Status checking:
launchctl list | grep -E "${PLIST_BACKGROUND%.plist}$"

# Pause flag detection:
if [ -f "$PAUSE_FLAG_PATH" ] && [ "$label" == "${PLIST_BACKGROUND%.plist}" ]; then

# Service status function calls:
check_service "${PLIST_BACKGROUND%.plist}" "Main Service"
check_service "${PLIST_MENUBAR%.plist}" "Menu Bar App"
```

---

## 🔄 **Simplified Approach: Filename → Derived Label**

### **PLIST_BACKGROUND:**
- **Filename**: `"com.clipboardmonitor.service.dev.plist"`
- **Derived Label**: `"${PLIST_BACKGROUND%.plist}"` = `"com.clipboardmonitor.service.dev"`

### **PLIST_MENUBAR:**
- **Filename**: `"com.clipboardmonitor.menubar.dev.plist"`
- **Derived Label**: `"${PLIST_MENUBAR%.plist}"` = `"com.clipboardmonitor.menubar.dev"`

---

## 📊 **How They Work Together:**

### **1. Service Management (load/unload):**
```bash
# Uses PLIST_BACKGROUND (filename)
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_BACKGROUND"
```

### **2. Status Checking:**
```bash
# Uses derived label (service identifier)
launchctl list | grep -E "${PLIST_BACKGROUND%.plist}$"
```

### **3. Inside the Plist File:**
```xml
<key>Label</key>
<string>com.clipboardmonitor.service.dev</string>  <!-- This matches ${PLIST_BACKGROUND%.plist} -->
```

---

## 🎯 **Summary (UPDATED - Simplified Approach):**

| Variable | Type | Purpose | Used For |
|----------|------|---------|----------|
| `PLIST_BACKGROUND` | **Filename** | Main service plist file | `launchctl load/unload` + derive labels |
| `PLIST_MENUBAR` | **Filename** | Menu bar plist file | `launchctl load/unload` + derive labels |

### **✅ Benefits of the New Approach:**
- **✅ Reduced complexity**: Only 2 variables instead of 4
- **✅ No inconsistency risk**: Labels are always derived from filenames
- **✅ DRY principle**: Single source of truth per service
- **✅ Self-documenting**: Relationship between filename and label is obvious
- **✅ Less maintenance**: No need to keep separate label variables in sync

**The filename variables are the single source of truth - labels are derived dynamically when needed using `${VARIABLE%.plist}` parameter expansion.** 🚀
