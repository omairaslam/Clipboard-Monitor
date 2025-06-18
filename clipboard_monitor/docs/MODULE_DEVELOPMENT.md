# Module Development Guide

This guide explains how to create custom modules for the Clipboard Monitor application. The module system has been enhanced with shared utilities, improved security, and comprehensive safety guidelines.

## Module Structure

Each module should be a Python file in the `modules/` directory with a name ending in `_module.py`. For example:
- `markdown_module.py`
- `mermaid_module.py`
- `custom_module.py`

## Module Interface

Each module must implement the following function:

```python
def process(clipboard_content) -> bool:
    """
    Process clipboard content and optionally modify it.
    
    Args:
        clipboard_content (str): The current clipboard content
        
    Returns:
        bool: True if the clipboard was modified, False otherwise
    """
    # Your processing logic here
    pass
```

The `process` function should:
1. Accept a string parameter containing the clipboard content
2. Return `True` if the clipboard was modified, `False` otherwise

## Module Loading Process

1. The main application scans the `modules/` directory for Python files ending with `_module.py`
2. Each module is imported dynamically
3. The module is validated to ensure it has a callable `process` function
4. Valid modules are added to the processing pipeline
5. Invalid modules are logged and skipped

## Shared Utilities

The application provides a comprehensive `utils.py` module with essential utilities for module development:

### Available Utilities

```python
from utils import (
    show_notification,           # Secure notification system
    validate_string_input,       # Input validation
    safe_expanduser,            # Secure path expansion
    safe_subprocess_run,        # Safe subprocess execution
    ContentTracker,             # Loop prevention
    ensure_directory_exists     # Safe directory creation
)
```

### Key Features
- **Security Hardened**: All utilities include security measures and input validation
- **Thread Safe**: Proper locking and synchronization for concurrent operations
- **Error Resilient**: Comprehensive error handling with graceful degradation
- **Performance Optimized**: Efficient implementations with minimal overhead

## Best Practices

### Thread Safety

Always use locks for thread safety:

```python
import threading

# Create a lock for thread-safe operations
_processing_lock = threading.Lock()

def process(clipboard_content) -> bool:
    # Use the lock to prevent concurrent processing
    with _processing_lock:
        # Your processing logic here
        pass
```

### Loop Prevention

Use the ContentTracker utility to prevent processing loops:

```python
from utils import ContentTracker

# Create a content tracker
_content_tracker = ContentTracker(max_history=5)

def process(clipboard_content) -> bool:
    # Check if content was recently processed
    if _content_tracker.has_processed(clipboard_content):
        return False

    # Process content
    # ...

    # Track this content to prevent reprocessing
    _content_tracker.add_content(clipboard_content)
```

### Input Validation

Always validate input using the shared utility:

```python
from utils import validate_string_input

def process(clipboard_content) -> bool:
    # Validate input
    if not validate_string_input(clipboard_content, "clipboard_content"):
        return False

    # Process content
    # ...
```

### Path Handling

Use secure path expansion for all file operations:

```python
from utils import safe_expanduser, ensure_directory_exists

def save_data(data, filename):
    # Secure path expansion
    file_path = safe_expanduser(f"~/Library/Application Support/ClipboardMonitor/{filename}")

    # Ensure directory exists
    directory = os.path.dirname(file_path)
    ensure_directory_exists(directory)

    # Save data
    with open(file_path, 'w') as f:
        f.write(data)
```

### Content Sanitization

For modules that process structured content (like Mermaid diagrams), implement proper sanitization to prevent parsing errors and security issues:

```python
import re

def sanitize_content(content):
    """Sanitize content to escape problematic characters"""
    try:
        # Example: Sanitize parentheses in Mermaid node text
        # Pattern to find node text (content inside square brackets, curly braces, or quotes)
        node_text_pattern = r'(\[[^\]]*\]|\{[^}]*\}|"[^"]*")'

        def sanitize_node_text(match):
            text = match.group(0)
            # If it's a bracketed text [like this]
            if text.startswith('[') and text.endswith(']'):
                # Replace parentheses with dashes for better readability
                inner_text = text[1:-1]
                sanitized_text = inner_text.replace('(', ' - ').replace(')', '')
                # Clean up any double spaces
                sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()
                return f"[{sanitized_text}]"
            # If it's a curly brace text {like this}
            elif text.startswith('{') and text.endswith('}'):
                inner_text = text[1:-1]
                sanitized_text = inner_text.replace('(', ' - ').replace(')', '')
                sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()
                return f"{{{sanitized_text}}}"
            # If it's quoted text "like this"
            elif text.startswith('"') and text.endswith('"'):
                inner_text = text[1:-1]
                sanitized_text = inner_text.replace('(', ' - ').replace(')', '')
                sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()
                return f'"{sanitized_text}"'
            return text

        # Replace node text with sanitized version
        sanitized_content = re.sub(node_text_pattern, sanitize_node_text, content)

        logger.debug(f"Sanitized content: {sanitized_content}")
        return sanitized_content
    except Exception as e:
        logger.error(f"[bold red]Error sanitizing content:[/bold red] {str(e)}")
        # Return original content if sanitization fails
        return content

def process(clipboard_content) -> bool:
    # Validate input
    if not validate_string_input(clipboard_content, "clipboard_content"):
        return False

    # Sanitize content before processing
    sanitized_content = sanitize_content(clipboard_content)

    # Process sanitized content
    # ...
```

**Key Sanitization Principles:**
- **Replace problematic characters** with safe alternatives (e.g., parentheses → dashes)
- **Support all node types** (square brackets, curly braces, quotes)
- **Maintain readability** by using meaningful replacements
- **Validate input format** before processing
- **Handle sanitization errors gracefully** by returning original content
- **Log sanitization actions** for debugging
- **Test with problematic input** to ensure robustness

## Clipboard Safety Guidelines

**IMPORTANT**: Modules should never modify clipboard content without explicit user consent. Follow these safety principles:

### **Default Behavior: Read-Only**
```python
def process(clipboard_content) -> bool:
    # Always check configuration before modifying clipboard
    module_config = load_module_config()
    modify_clipboard = module_config.get('your_module_modify_clipboard', False)

    if is_your_content_type(clipboard_content):
        if modify_clipboard:
            # Only modify if explicitly enabled
            modified_content = process_content(clipboard_content)
            pyperclip.copy(modified_content)
            show_notification("Content Processed", "Content modified and copied to clipboard")
            return True
        else:
            # Read-only mode: detect and notify only
            show_notification("Content Detected", "Content detected (read-only mode)")
            return False  # Don't modify clipboard

    return False
```

### **Configuration Loading**
```python
import json
import os

def load_module_config():
    """Load module configuration from config.json"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('modules', {})
    except Exception as e:
        logger.error(f"Error loading module config: {e}")
    return {}
```

### **Safety Principles**
1. **Never modify clipboard by default** - require explicit user configuration
2. **Clear notifications** - distinguish between detection and modification
3. **Conservative defaults** - prioritize content protection over convenience
4. **User control** - provide menu bar toggles for clipboard modification
5. **Content type respect** - only process content you're designed for
6. **Graceful fallback** - handle configuration errors safely

### **Content Type Guidelines**
- ✅ **Process only your target content** (e.g., markdown, code, diagrams)
- ❌ **Never modify plain text, URLs, emails, JSON** unless specifically designed for them
- ✅ **Provide clear detection logic** with strict validation
- ❌ **Avoid broad pattern matching** that could catch unintended content

### **User Experience Best Practices**
- **Clear notifications**: "Markdown detected (read-only mode)" vs "Markdown converted to RTF"
- **Consistent behavior**: Same detection logic whether modifying or not
- **Immediate feedback**: Show notifications for both detection and modification
- **Reversible actions**: Users should be able to undo or disable modifications

### Error Handling

Use try-except blocks to catch and log errors:

```python
import logging
logger = logging.getLogger("my_module")

def process(clipboard_content) -> bool:
    try:
        # Process content
        # ...
    except Exception as e:
        logger.error(f"Error processing content: {e}")
        return False
```

## Logging

Use the rich logging system:

```python
from rich.console import Console
import logging

console = Console()
logger = logging.getLogger("my_module")

def process(clipboard_content) -> bool:
    # Log with colors and formatting
    logger.info("[cyan]Processing content...[/cyan]")
    logger.error("[bold red]Error occurred![/bold red]")
    logger.warning("[yellow]Warning message[/yellow]")
    logger.debug("Debug information")
```

## Notifications

Use the enhanced notification system from utils:

```python
from utils import show_notification

def process(clipboard_content) -> bool:
    # Show a notification with security and reliability features
    show_notification("Title", "Message")

    # The notification system includes:
    # - Input sanitization to prevent AppleScript injection
    # - Timeout protection (3 seconds)
    # - Error logging for debugging
    # - Thread safety for macOS
```

### **Notification Best Practices**

#### **Security Guidelines**
```python
# ✅ Good: Use the shared notification function
from utils import show_notification
show_notification("Safe Title", "Safe message")

# ❌ Bad: Direct AppleScript without sanitization
subprocess.run(["osascript", "-e", f'display notification "{unsafe_message}"'])
```

#### **Context-Aware Notifications**
```python
def process(clipboard_content) -> bool:
    if modify_clipboard:
        show_notification("Content Processed", "Content modified and copied to clipboard")
        return True
    else:
        show_notification("Content Detected", "Content detected (read-only mode)")
        return False
```

#### **Error Handling**
```python
def process(clipboard_content) -> bool:
    try:
        # Process content
        result = process_content(clipboard_content)
        show_notification("Success", "Content processed successfully")
        return True
    except Exception as e:
        show_notification("Error", f"Processing failed: {str(e)}")
        return False
```

### **Notification Features**
- **Security Hardened**: Input sanitization prevents AppleScript injection
- **Timeout Protected**: 3-second timeout prevents hanging
- **Error Logged**: Failed notifications logged for debugging
- **Thread Safe**: Proper main thread handling for macOS
- **Fallback System**: Multiple delivery methods ensure reliability

## Example Module

Here's a complete example module that processes text by converting it to uppercase:

```python
import threading
import logging
import json
import os
from rich.console import Console
import sys

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import show_notification, validate_string_input, ContentTracker

# Set up rich logging
console = Console()
logger = logging.getLogger("uppercase_module")

# Global content tracker to prevent processing loops
_content_tracker = ContentTracker(max_history=5)
_processing_lock = threading.Lock()

def load_module_config():
    """Load module configuration from config.json"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('modules', {})
    except Exception as e:
        logger.error(f"Error loading module config: {e}")
    return {}

def process(clipboard_content) -> bool:
    """Convert clipboard text to uppercase (with safety controls)"""

    # Prevent concurrent processing and loops
    with _processing_lock:
        # Safety check for None or empty content
        if not validate_string_input(clipboard_content, "clipboard_content"):
            return False

        # Prevent processing the same content repeatedly
        if _content_tracker.has_processed(clipboard_content):
            logger.debug("Skipping uppercase processing - content already processed recently")
            return False

        try:
            # Check if clipboard modification is enabled for this module
            module_config = load_module_config()
            modify_clipboard = module_config.get('uppercase_modify_clipboard', False)  # Default to read-only

            # Convert to uppercase
            uppercase_text = clipboard_content.upper()

            # Only process if the content actually changed
            if uppercase_text != clipboard_content:
                # Track this content to prevent reprocessing
                _content_tracker.add_content(clipboard_content)

                if modify_clipboard:
                    # Modification mode: actually change clipboard
                    logger.info("[cyan]Converting text to uppercase...[/cyan]")
                    show_notification("Text Conversion", "Converting text to uppercase...")

                    # Copy uppercase text back to clipboard
                    import pyperclip
                    pyperclip.copy(uppercase_text)

                    logger.info("[green]Text converted to uppercase and copied to clipboard![/green]")
                    show_notification("Text Converted", "Uppercase text copied to clipboard!")
                    return True  # Indicate that content was processed
                else:
                    # Read-only mode: detect and notify only
                    logger.info("[cyan]Uppercase conversion available (read-only mode)[/cyan]")
                    show_notification("Text Detected", "Uppercase conversion available (read-only mode)")
                    return False  # Don't modify clipboard

            return False  # Content didn't change

        except Exception as e:
            logger.error(f"[bold red]Error processing text:[/bold red] {e}")
            return False
```

## Testing Your Module

1. Place your module in the `modules/` directory
2. Restart the Clipboard Monitor service
3. Check the logs to ensure your module was loaded
4. Test with appropriate clipboard content
5. Verify that your module processes the content correctly

## Debugging Tips

1. Run the main script directly with debug logging:
   ```bash
   python3 main.py --debug
   ```

2. Add debug print statements to your module:
   ```python
   logger.debug(f"Content: {clipboard_content[:100]}...")
   ```

3. Test your module's process function directly:
   ```python
   if __name__ == "__main__":
       test_content = "Test content"
       result = process(test_content)
       print(f"Process result: {result}")
   ```

## Common Issues

### Module Not Loading
- Check the file name (must end with `_module.py`)
- Verify the module has a `process` function
- Check for syntax errors
- Look for import errors in the logs

### Module Not Processing
- Verify the content detection logic
- Check if the module is enabled in config.json
- Look for errors in the logs
- Verify the module is returning the correct boolean value

### Clipboard Not Updating
- Check if pyperclip is working correctly
- Verify the module is returning True when it modifies the clipboard
- Look for errors in the logs
