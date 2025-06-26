# Clipboard Monitoring Methods

This document explains the different clipboard monitoring methods used in the Clipboard Monitor application and their performance characteristics. 

**Note:** All logging in the application is now plain text with timestamps, padded log levels, section separators, and multi-line support. No colorized or Rich formatting is used anywhere in the application (June 2025).

## Overview

The application uses two different methods for monitoring clipboard changes:

1. **Enhanced Monitoring** (macOS-specific using pyobjc)
2. **Polling Monitoring** (fallback method)

The application automatically selects the best available method based on the environment and available libraries.

## Enhanced Monitoring (macOS)

### Implementation

Enhanced monitoring uses the native macOS Cocoa framework through pyobjc to efficiently detect clipboard changes.

```python
@objc.selector
def checkClipboardChange_(self, timer):
    """
    Timer callback method that checks for clipboard changes using changeCount.
    This is more efficient than polling the actual clipboard content.
    """
    current_change_count = self.pasteboard.changeCount()
    if current_change_count != self.last_change_count:
        self.last_change_count = current_change_count
        # Only read clipboard content when a change is detected
        current_clipboard_content = pyperclip.paste()
        # Process the content...
```

### Characteristics

- **Efficiency**: Very high
- **Responsiveness**: Checks every 0.1 seconds
- **CPU Usage**: Minimal (<0.1% on average)
- **Memory Usage**: Minimal
- **Battery Impact**: Negligible
- **Dependencies**: Requires `pyobjc-framework-Cocoa`

### How It Works

1. Uses `NSTimer` to run a check every 0.1 seconds
2. Calls `pasteboard.changeCount()` to get the current change counter
3. Only reads the actual clipboard content if the counter has changed
4. This avoids the expensive operation of reading clipboard content when nothing has changed

## Polling Monitoring (Fallback)

### Implementation

Polling monitoring uses a simple loop that periodically checks the clipboard content.

```python
while True:
    clipboard_content = pyperclip.paste()
    if clipboard_content != last_clipboard:
        last_clipboard = clipboard_content
        # Process the content...
    time.sleep(CONFIG['polling_interval'])  # Default: 1.0 second
```

### Characteristics

- **Efficiency**: Moderate
- **Responsiveness**: Checks every 1.0 seconds (configurable)
- **CPU Usage**: 0.5-2% depending on clipboard content size
- **Memory Usage**: Moderate (depends on clipboard content size)
- **Battery Impact**: Low to moderate
- **Dependencies**: Only requires `pyperclip`

### How It Works

1. Runs in a continuous loop with a sleep interval
2. Reads the entire clipboard content on each iteration
3. Compares the content with the previously saved content
4. Processes the content only if it has changed

## Performance Comparison

| Aspect | Enhanced Monitoring | Polling Monitoring |
|--------|---------------------|-------------------|
| CPU Usage | <0.1% | 0.5-2% |
| Memory Footprint | Minimal | Depends on clipboard size |
| Battery Impact | Negligible | Low to moderate |
| Responsiveness | 0.1s | 1.0s (configurable) |
| Platform Support | macOS only | Cross-platform |

## Recommendations

- **macOS Users**: Ensure `pyobjc-framework-Cocoa` is installed to use the enhanced monitoring method
- **Other Platforms**: Only polling monitoring is available
- **Battery-Sensitive**: Enhanced monitoring is strongly recommended for laptop users
- **Large Clipboard Content**: Enhanced monitoring provides significant benefits when frequently copying large content

## Troubleshooting


If the application is falling back to polling mode when you expect enhanced mode:

1. **Verify that `pyobjc-framework-Cocoa` is installed:**
   ```bash
   pip3 list | grep pyobjc
   ```

2. **Ensure the correct Python interpreter is being used in the LaunchAgent plist file.**

3. **Check the logs for import errors:**
   ```bash
   tail -f ~/Library/Logs/ClipboardMonitor.out.log | grep pyobjc
   ```

4. **Try reinstalling the dependency:**
   ```bash
   pip3 install --upgrade pyobjc-framework-Cocoa
   ```

5. **Full Disk Access Reset (macOS Security):**
   - Go to **System Settings** → **Privacy & Security** → **Full Disk Access**.
   - Find the entry for your `python3` service (or the Python interpreter used by Clipboard Monitor).
   - **Revoke Full Disk Access** for this Python service.
   - **Re-add Full Disk Access** by clicking the `+` button and selecting the same Python interpreter again.
   - Restart the Clipboard Monitor service.

> This step resolves cases where macOS security prevents enhanced clipboard monitoring even when all dependencies are installed.