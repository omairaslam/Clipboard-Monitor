"""
Application Constants
Centralized constants for timeouts, intervals, size limits, and other configuration values.
"""

# Timing Constants (in seconds)
DEFAULT_POLLING_INTERVAL = 1.0
DEFAULT_ENHANCED_CHECK_INTERVAL = 0.1
DEFAULT_IDLE_CHECK_INTERVAL = 1.0
DEFAULT_MODULE_VALIDATION_TIMEOUT = 5.0

# Timer intervals for different scenarios
TIMER_INTERVAL_ACTIVE = 0.1      # Enhanced mode active checking
TIMER_INTERVAL_IDLE = 1.0        # Reduced frequency during idle
PAUSE_CHECK_INTERVAL = 1.0       # Time between pause flag checks
ERROR_RETRY_DELAY = 1.0          # Brief pause before retrying after error
PYPERCLIP_ERROR_DELAY = 5.0      # Longer wait for persistent pyperclip issues

# Size Limits
DEFAULT_MAX_CLIPBOARD_SIZE = 10485760    # 10MB in bytes
DEFAULT_MAX_CONTENT_LENGTH = 10000       # Maximum content length for history storage
DEFAULT_MAX_HISTORY_ITEMS = 100          # Maximum number of items in history

# Error Handling
MAX_CONSECUTIVE_ERRORS = 10              # Maximum consecutive errors before exit
CONTENT_TRACKER_MAX_HISTORY = 5          # Maximum content history for deduplication

# File Detection Thresholds
CODE_DETECTION_THRESHOLD = 0.15          # Minimum ratio of code lines to total lines
MARKDOWN_DETECTION_THRESHOLD = 0.25      # Minimum ratio of markdown lines to total lines
MIN_LINES_FOR_CODE_DETECTION = 3        # Minimum lines needed to detect code

# System Idle Thresholds (in seconds)
SYSTEM_IDLE_THRESHOLD = 60               # Time before reducing check frequency

# UI/Menu Constants
MENU_REFRESH_DELAY = 0.01               # Small delay for UI updates
TEST_CLIPBOARD_DELAY = 0.1              # Delay for clipboard operations in tests
CLEAR_HISTORY_CONFIRMATION_DELAY = 1.5   # Delay for user confirmation

# Polling Interval Options (for menu)
POLLING_INTERVALS = {
    "0.5s (Faster)": 0.5,
    "1.0s (Default)": 1.0,
    "2.0s (Battery Saving)": 2.0,
    "5.0s (Power Saving)": 5.0
}

ENHANCED_CHECK_INTERVALS = {
    "0.05s (Ultra Fast)": 0.05,
    "0.1s (Default)": 0.1,
    "0.2s (Balanced)": 0.2,
    "0.5s (Conservative)": 0.5
}

# Configuration Defaults
DEFAULT_HISTORY_CONFIG = {
    "max_items": DEFAULT_MAX_HISTORY_ITEMS,
    "max_content_length": DEFAULT_MAX_CONTENT_LENGTH,
    "save_location": "~/Library/Application Support/ClipboardMonitor/clipboard_history.json"
}

DEFAULT_GENERAL_CONFIG = {
    'polling_interval': DEFAULT_POLLING_INTERVAL,
    'module_validation_timeout': DEFAULT_MODULE_VALIDATION_TIMEOUT,
    'enhanced_check_interval': DEFAULT_ENHANCED_CHECK_INTERVAL,
    'idle_check_interval': DEFAULT_IDLE_CHECK_INTERVAL,
    'debug_mode': False,
    'notification_title': 'Clipboard Monitor'
}

DEFAULT_SECURITY_CONFIG = {
    'max_clipboard_size': DEFAULT_MAX_CLIPBOARD_SIZE,
    'sanitize_clipboard': True
}

DEFAULT_PERFORMANCE_CONFIG = {
    'lazy_module_loading': True,
    'adaptive_checking': True,
    'memory_optimization': True,
    'process_large_content': True,
    'max_module_execution_time': 500
}

DEFAULT_MODULES_CONFIG = {
    'markdown_modify_clipboard': True,
    'code_formatter_modify_clipboard': False,
    'mermaid_modify_clipboard': False, # This likely refers to modifying clipboard content, not URL copying or browser opening
    'mermaid_copy_url': False, # Default for copying URL specifically for Mermaid
    'mermaid_open_in_browser': True, # Default for opening browser for Mermaid
    'mermaid_theme': "default", # Options: "default", "dark", "forest", "neutral"
    'history_enabled': True,
    # Draw.io specific URL parameters
    'drawio_copy_url': True, # Existing setting, kept for clarity
    'drawio_open_in_browser': True, # Existing setting, kept for clarity
    'drawio_lightbox': True,
    'drawio_edit_mode': "_blank", # e.g., "_blank", "local", "device"
    'drawio_layers': True,
    'drawio_nav': True,
}

# Mermaid themes for menu
MERMAID_THEMES = {
    "Default": "default",
    "Dark": "dark",
    "Forest": "forest",
    "Neutral": "neutral"
}

# Draw.io edit modes for menu
DRAWIO_EDIT_MODES = {
    "New Tab (_blank)": "_blank",
    "Local": "local", # Assuming "local" is a valid option, placeholder
    "Device": "device"  # Assuming "device" is a valid option, placeholder
}


# Complete default configuration
DEFAULT_CONFIG = {
    'general': DEFAULT_GENERAL_CONFIG,
    'history': DEFAULT_HISTORY_CONFIG,
    'security': DEFAULT_SECURITY_CONFIG,
    'performance': DEFAULT_PERFORMANCE_CONFIG,
    'modules': DEFAULT_MODULES_CONFIG
}
