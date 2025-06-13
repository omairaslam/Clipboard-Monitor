# Clipboard Monitor - Bug Fixes and Improvements

This document outlines the bugs that were identified and fixed in the clipboard monitor application.

## Issues Fixed

### 1. **Unused Import (Minor)**
- **Issue**: `NSRunLoop` was imported but never used
- **Fix**: Removed the unused import from `main.py`

### 2. **Race Condition in Markdown Module**
- **Issue**: The markdown module modified the clipboard twice in quick succession (RTF then original), causing potential race conditions with event-driven monitoring
- **Fix**: 
  - Removed the clipboard restoration to avoid race conditions
  - Added content tracking to prevent reprocessing the same content
  - Added thread-safe processing with locks

### 3. **Inconsistent Error Handling**
- **Issue**: Mixed error handling patterns throughout the codebase
- **Fix**: 
  - Standardized error handling with specific exception types
  - Added proper `pyperclip.PyperclipException` handling
  - Added timeout handling for subprocess calls

### 4. **Potential Infinite Loop in Event-Driven Mode**
- **Issue**: Module clipboard modifications could trigger new events, causing infinite loops
- **Fix**: 
  - Added processing flags to prevent recursive processing
  - Implemented content hashing to detect and prevent processing loops
  - Added proper cleanup in event handlers

### 5. **Module Loading Error Handling**
- **Issue**: No error handling for missing directories, syntax errors, or missing functions
- **Fix**: 
  - Added directory existence checks
  - Added module validation to ensure required `process` function exists
  - Added comprehensive error handling for module loading failures
  - Skip invalid modules instead of crashing

### 6. **Hardcoded Notification Title**
- **Issue**: Notification title was hardcoded with personal name
- **Fix**: 
  - Made notification title configurable through `CONFIG` dictionary
  - Default title is now generic "Clipboard Monitor"

### 7. **Duplicate Notification Function**
- **Issue**: Both `main.py` and `markdown_module.py` had identical `show_notification` functions
- **Fix**: 
  - Created shared `utils.py` module with common utilities
  - Removed duplicate functions
  - Added better error handling and security (AppleScript injection prevention)

### 8. **Missing Module Interface Validation**
- **Issue**: Code assumed all modules had `process` function without validation
- **Fix**: 
  - Added `_validate_module()` function to check module interface
  - Validates both existence and callability of `process` function
  - Logs clear error messages for invalid modules

### 9. **Logging Level Configuration Issue**
- **Issue**: Used string `"NOTSET"` instead of proper logging constant
- **Fix**: Changed to `logging.INFO` for proper logging configuration

### 10. **Potential Memory Leak in Event Handler**
- **Issue**: Event handler stored references without cleanup mechanisms
- **Fix**: 
  - Added `cleanup()` method to event handler
  - Proper resource cleanup in finally blocks
  - Limited content history to prevent unbounded memory growth

## New Features Added

### Configuration System
- Added `CONFIG` dictionary for easy configuration management
- Configurable notification title, polling interval, and timeouts

### Shared Utilities (`utils.py`)
- `show_notification()`: Secure notification function with AppleScript injection prevention
- `validate_string_input()`: Input validation utility
- `safe_subprocess_run()`: Safe subprocess execution with timeout
- `ContentTracker`: Utility class to prevent processing loops

### Enhanced Error Handling
- Timeout handling for all subprocess calls
- Consecutive error counting with automatic shutdown
- Better logging with context information
- Graceful degradation when dependencies are missing

### Thread Safety
- Added locks to prevent concurrent processing
- Safe cleanup mechanisms
- Proper resource management

## Testing Improvements

### Markdown Module Testing
- Added comprehensive test cases for edge cases
- Better test output with clear pass/fail indicators
- Tests for None values, empty strings, and invalid input

## Security Improvements

### AppleScript Injection Prevention
- Proper escaping of quotes in notification messages
- Input validation to prevent malicious script execution

## Performance Improvements

### Reduced Processing Overhead
- Content hashing to avoid unnecessary processing
- Limited history tracking to prevent memory bloat
- Configurable polling intervals

## Backward Compatibility

All changes maintain backward compatibility with existing module interfaces. Existing modules will continue to work without modification, but will benefit from the improved error handling and loop prevention.

## Configuration Options

The following configuration options are now available in `main.py`:

```python
CONFIG = {
    'notification_title': 'Clipboard Monitor',  # Customizable notification title
    'polling_interval': 1.0,                    # Polling interval in seconds
    'module_validation_timeout': 5.0            # Module validation timeout
}
```

## Dependencies

No new dependencies were added. All improvements use existing libraries and Python standard library features.
