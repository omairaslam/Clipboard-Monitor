"""
Shared utilities for the Clipboard Monitor application.
"""

import subprocess
import hashlib
import logging
import re
import threading
import os
import pwd
from pathlib import Path
import json
import pyperclip

logger = logging.getLogger("utils")

def setup_logging(out_log_path=None, err_log_path=None):
    """Set up logging to unified log files (matches plist)."""
    import logging
    import sys
    # Use unified log paths if not provided
    paths = get_app_paths()
    out_log = out_log_path or paths["out_log"]
    err_log = err_log_path or paths["err_log"]

    # Ensure parent directories for log files exist
    for log_path in [out_log, err_log]:
        dir_path = os.path.dirname(log_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

    # Remove all handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Set up root logger
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)-5s] | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(out_log, mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Set up error logger
    error_logger = logging.getLogger("error")
    error_handler = logging.FileHandler(err_log, mode='a')
    error_handler.setLevel(logging.WARNING)
    error_logger.addHandler(error_handler)

def show_notification(title, subtitle=None, message=None, *args, **kwargs):
    """
    Show a notification using AppleScript (macOS).
    Args:
        title (str): The notification title
        subtitle (str, optional): The notification subtitle (ignored in AppleScript, included for compatibility)
        message (str, optional): The notification message
    """
    try:
        # Sanitize inputs to prevent AppleScript injection
        title = validate_string_input(title, "title", default="Notification")
        if subtitle is not None:
            subtitle = validate_string_input(subtitle, "subtitle", default="")
        if message is None and subtitle is not None:
            message = subtitle
        elif message is None:
            message = ""
        else:
            message = validate_string_input(message, "message", default="")

        # Escape quotes to prevent AppleScript injection
        title = title.replace('"', '\"')
        message = message.replace('"', '\"')

        # Show notification using AppleScript
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}"'
        ], check=True, timeout=3)

        logger.debug(f"Notification shown: {title} - {message}")
    except subprocess.TimeoutExpired:
        logger.error("Notification timed out")
    except Exception as e:
        logger.error(f"Notification error: {str(e)}")

def _sanitize_applescript_string(s: str) -> str:
    """Sanitize a string for safe inclusion in an AppleScript string literal."""
    if not isinstance(s, str): # Ensure it's a string, convert if not
        s = str(s)
    s = s.replace('\\', '\\\\')  # Escape backslashes first
    s = s.replace('"', '\\"')    # Escape double quotes
    return s

def show_notification(title, subtitle=None, message=None, *args, **kwargs):
    """
    Show a notification using AppleScript (macOS).
    Args:
        title (str): The notification title
        subtitle (str, optional): The notification subtitle (used in message if message is None)
        message (str, optional): The notification message
    """
    try:
        # Validate inputs first (ensure they are strings, non-empty if possible)
        title_str = validate_string_input(title, "title", default="Notification")

        # Determine message content
        if message is None and subtitle is not None:
            message_str = validate_string_input(subtitle, "subtitle_as_message", default="")
        elif message is None:
            message_str = ""
        else:
            message_str = validate_string_input(message, "message", default="")

        # Sanitize for AppleScript
        sanitized_title = _sanitize_applescript_string(title_str)
        sanitized_message = _sanitize_applescript_string(message_str)

        # Subtitle is not directly used in `display notification` if message is present.
        # If it were to be added, it would need sanitization too.
        # For now, we'll just use title and message.

        script = f'display notification "{sanitized_message}" with title "{sanitized_title}"'

        # Show notification using AppleScript
        subprocess.run([
            "osascript", "-e",
            script
        ], check=True, timeout=3)

        logger.debug(f"Notification shown: Title='{title_str}', Message='{message_str}' (Sanitized: Title='{sanitized_title}', Message='{sanitized_message}')")
    except subprocess.TimeoutExpired:
        logger.error("Notification timed out")
    except Exception as e:
        logger.error(f"Notification error: {str(e)}")


def validate_string_input(value, param_name, default=None):
    """
    Validate that a value is a non-empty string.
    
    Args:
        value: The value to validate
        param_name (str): The parameter name for error messages
        default: Default value to return if validation fails
        
    Returns:
        str: The validated string or default value
    """
    if value is None:
        logger.warning(f"Parameter '{param_name}' is None, using default")
        return default
    
    if not isinstance(value, str):
        logger.warning(f"Parameter '{param_name}' is not a string, using default")
        return default
    
    if not value.strip():
        logger.warning(f"Parameter '{param_name}' is empty, using default")
        return default
    
    return value

def safe_subprocess_run(cmd, timeout=5, check=True):
    """
    Safely run a subprocess command with timeout.
    
    Args:
        cmd (list): Command and arguments
        timeout (int): Timeout in seconds
        check (bool): Whether to check return code
        
    Returns:
        subprocess.CompletedProcess: The completed process
        
    Raises:
        subprocess.TimeoutExpired: If the command times out
        subprocess.CalledProcessError: If the command fails and check=True
    """
    try:
        return subprocess.run(
            cmd,
            check=check,
            timeout=timeout,
            capture_output=True,
            text=True
        )
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        raise e
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with code {e.returncode}: {' '.join(cmd)}")
        logger.error(f"Error output: {e.stderr}")
        raise e
    except Exception as e:
        logger.error(f"Error running command: {' '.join(cmd)}")
        logger.error(f"Exception: {str(e)}")
        raise e

def get_home_directory():
    """
    Get the user's home directory using multiple fallback methods.
    This is more robust than os.path.expanduser("~") when working directory
    is set to something other than the home directory.

    Returns:
        str: The absolute path to the user's home directory
    """
    try:
        # Method 1: Use pathlib.Path.home() (most reliable)
        home_path = str(Path.home())
        if home_path and os.path.isdir(home_path):
            logger.debug(f"Home directory found via Path.home(): {home_path}")
            return home_path
    except Exception as e:
        logger.debug(f"Path.home() failed: {e}")

    try:
        # Method 2: Use HOME environment variable
        home_env = os.environ.get('HOME')
        if home_env and os.path.isdir(home_env):
            logger.debug(f"Home directory found via HOME env: {home_env}")
            return home_env
    except Exception as e:
        logger.debug(f"HOME environment variable failed: {e}")

    try:
        # Method 3: Use pwd module to get user info
        user_info = pwd.getpwuid(os.getuid())
        home_pwd = user_info.pw_dir
        if home_pwd and os.path.isdir(home_pwd):
            logger.debug(f"Home directory found via pwd: {home_pwd}")
            return home_pwd
    except Exception as e:
        logger.debug(f"pwd module failed: {e}")

    try:
        # Method 4: Fallback to os.path.expanduser (original method)
        home_expand = os.path.expanduser("~")
        # Only use this if it doesn't create a literal ~ path
        if home_expand != "~" and os.path.isdir(home_expand):
            logger.debug(f"Home directory found via expanduser: {home_expand}")
            return home_expand
    except Exception as e:
        logger.debug(f"expanduser failed: {e}")


    raise RuntimeError("Unable to determine user home directory using any method")

def safe_expanduser(path):
    """
    Safely expand user home directory in paths, with robust fallback methods and directory traversal prevention.
    This prevents the creation of literal ~ folders and blocks directory traversal.

    Args:
        path (str): Path that may contain ~ for home directory

    Returns:
        str: Path with ~ properly expanded to home directory

    Raises:
        RuntimeError: If home directory cannot be determined or path is unsafe
    """
    if not isinstance(path, str):
        raise ValueError("Path must be a string")

    # If path doesn't start with ~, return as-is
    if not path.startswith("~"):
        expanded = path
    else:
        try:
            # Get the home directory using our robust method
            home_dir = get_home_directory()

            # Handle different tilde patterns
            if path == "~":
                expanded = home_dir
            elif path.startswith("~/"):
                expanded = os.path.join(home_dir, path[2:])
            elif path.startswith("~"):
                # Handle ~username patterns (though less common)
                expanded = os.path.expanduser(path)
            else:
                expanded = path
        except Exception as e:
            logger.error(f"Failed to expand path '{path}': {e}")
            raise RuntimeError(f"Unable to expand user path: {path}")

    # Directory traversal prevention: block ../ or ..\\ in any part of the path
    if any(part in expanded for part in ["../", "..\\"]):
        logger.error(f"Blocked directory traversal attempt in path: {expanded}")
        raise RuntimeError(f"Directory traversal detected in path: {expanded}")

    return expanded

def ensure_directory_exists(path):
    """
    Ensure that a directory exists, creating it if necessary.

    Args:
        path (str): Directory path to ensure exists

    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        # Expand any ~ in the path first
        expanded_path = safe_expanduser(path)

        # Create directory if it doesn't exist
        os.makedirs(expanded_path, exist_ok=True)

        # Verify it exists and is a directory
        if os.path.isdir(expanded_path):
            logger.debug(f"Directory ensured: {expanded_path}")
            return True
        else:
            logger.error(f"Path exists but is not a directory: {expanded_path}")
            return False

    except Exception as e:
        logger.error(f"Failed to ensure directory exists: {path} -> {e}")
        return False

class ContentTracker:
    """
    Track content to prevent processing loops.
    
    This class maintains a history of processed content hashes
    to prevent the same content from being processed multiple times.
    """
    
    def __init__(self, max_history=10):
        """
        Initialize the content tracker.
        
        Args:
            max_history (int): Maximum number of content hashes to track
        """
        self.max_history = max_history
        self.content_hashes = []
        self.lock = threading.Lock()
        self.content_sizes = {}  # Track content sizes
        
    def add_content(self, content):
        """
        Add content to the tracker.
        
        Args:
            content (str): The content to track
        """
        if not content:
            return
        
        content_hash = self._hash_content(content)
        content_size = len(content)
        
        with self.lock:
            # Add to the front of the list
            self.content_hashes.insert(0, content_hash)
            self.content_sizes[content_hash] = content_size
            
            # Trim the list if needed
            if len(self.content_hashes) > self.max_history:
                old_hash = self.content_hashes.pop()
                if old_hash in self.content_sizes:
                    del self.content_sizes[old_hash]
    
    def has_processed(self, content):
        """
        Check if content has been processed recently.
        
        Args:
            content (str): The content to check
            
        Returns:
            bool: True if the content has been processed recently
        """
        if not content:
            return False
        
        content_hash = self._hash_content(content)
        
        with self.lock:
            return content_hash in self.content_hashes
    
    def _hash_content(self, content):
        """
        Create a hash of the content.
        
        Args:
            content (str): The content to hash
            
        Returns:
            str: The content hash
        """
        # Use faster hashing for large content
        if len(content) > 10000:
            # Only hash first and last 5000 chars for very large content
            return hashlib.md5((content[:5000] + content[-5000:]).encode('utf-8')).hexdigest()
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def clear(self):
        """Clear all tracked content."""
        with self.lock:
            self.content_hashes = []
            self.content_sizes.clear()

def get_app_paths():
    """Return a dict of important app paths, unified with plist log locations."""
    # Use the same log paths as in the LaunchAgent plist
    log_dir = Path(safe_expanduser("~/Library/Logs"))
    base_dir = Path(safe_expanduser("~/Library/Application Support/ClipboardMonitor"))
    return {
        "base_dir": str(base_dir),
        "history_file": str(base_dir / "clipboard_history.json"),
        "out_log": str(log_dir / "ClipboardMonitor.out.log"),
        "pause_flag": str(base_dir / "pause_flag"),
        "err_log": str(log_dir / "ClipboardMonitor.err.log"),
        "status_file": str(base_dir / "status.txt")
    }

def get_config(section=None, key=None, default=None):
    """
    Get configuration value from config.json using the centralized ConfigManager.
    Args:
        section (str, optional): The configuration section.
        key (str, optional): The key within the section.
        default: The default value to return if not found.
    Returns:
        The configuration value, section, or full config.
    """
    from config_manager import ConfigManager
    # Always create a new instance to ensure it loads the latest config,
    # especially important in tests where the config file is frequently changed.
    config_manager = ConfigManager()
    if section is None:
        return config_manager.config
    if key is None:
        return config_manager.get_section(section, default=default or {})
    return config_manager.get_config_value(section, key, default=default)

def set_config_value(section, key, value):
    """Set a configuration value in config.json"""
    try:
        config_path = Path(__file__).parent / 'config.json'

        # Load existing config
        if config_path.exists():
            with config_path.open('r') as f:
                config = json.load(f)
        else:
            config = {}

        # Ensure section exists
        if section not in config:
            config[section] = {}

        # Set the value
        config[section][key] = value

        # Save back to file
        with config_path.open('w') as f:
            json.dump(config, f, indent=2)

        return True
    except (OSError, json.JSONDecodeError, json.JSONEncodeError) as e:
        logger.error(f"Error setting config value {section}.{key}: {e}")
        return False

def load_clipboard_history():
    """
    Load clipboard history from the file specified in the configuration.
    This is the single source of truth for history loading.
    """
    try:
        # Get history file path from config, with a fallback default
        history_path_str = get_config('history', 'save_location', "~/Library/Application Support/ClipboardMonitor/clipboard_history.json")
        history_path = Path(safe_expanduser(history_path_str))

        if history_path.exists():
            with history_path.open('r') as f:
                history = json.load(f)
                return history
        return []
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Error loading clipboard history from {history_path}: {e}")
        return []

# Moved from main.py and ClipboardMonitorHandler
def get_clipboard_content():
    """Get clipboard content, trying multiple formats to capture RTF content."""
    try:
        # Try to get plain text first (most common case)
        try:
            text_content = subprocess.check_output(['pbpaste'],
                                                 universal_newlines=True,
                                                 timeout=2)
            if text_content and text_content.strip():
                logger.debug("Found plain text content in clipboard")
                return text_content
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass

        # If no plain text, try RTF content
        try:
            rtf_content = subprocess.check_output(['pbpaste', '-Prefer', 'rtf'],
                                                universal_newlines=True,
                                                timeout=2)
            if rtf_content and rtf_content.strip():
                logger.debug("Found RTF content in clipboard")
                return rtf_content
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass

        # Fallback to pyperclip
        try:
            pyperclip_content = pyperclip.paste()
            if pyperclip_content and pyperclip_content.strip():
                logger.debug("Found content via pyperclip")
                return pyperclip_content
        except pyperclip.PyperclipException:
            pass

        logger.debug("No clipboard content found")
        return None
    except Exception as e:
        logger.error(f"Error getting clipboard content: {e}")
        return None

def update_service_status(status):
    """Update the service status file
    
    Args:
        status: String status ('running_enhanced', 'running_polling', 'paused', 'error')
    """
    try:
        paths = get_app_paths()
        status_file = Path(paths["status_file"])
        ensure_directory_exists(str(status_file.parent))
        with status_file.open('w') as f:
            f.write(status)
    except OSError as e:
        logging.error(f"Error updating status file: {e}")

def get_service_status():
    """Get current service status from status file
    
    Returns:
        String status or 'unknown' if status file doesn't exist/can't be read
    """
    try:
        paths = get_app_paths()
        status_file = Path(paths["status_file"])
        if status_file.exists():
            with status_file.open('r') as f:
                return f.read().strip()
        return "unknown"
    except OSError:
        return "unknown"

def _write_log_header_if_needed(log_path, header):
    try:
        log_file = Path(log_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        if not log_file.exists() or log_file.stat().st_size == 0:
            with log_file.open('a') as f:
                f.write(header)
    except (OSError, PermissionError) as e:
        # This is a critical error, as logging is failing.
        # We can't use the logger here, so we print to stderr.
        import sys
        print(f"CRITICAL: Failed to write to log file {log_path}. Error: {e}", file=sys.stderr)

LOG_HEADER = (
    "=== Clipboard Monitor Output Log ===\n"
    "Created: {date}\n"
    "Format: [YYYY-MM-DD HH:MM:SS] [LEVEL ] | Message\n"
    "-------------------------------------\n"
).format(date=__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

ERR_LOG_HEADER = (
    "=== Clipboard Monitor Error Log ===\n"
    "Created: {date}\n"
    "Format: [YYYY-MM-DD HH:MM:SS] [LEVEL ] | Message\n"
    "-------------------------------------\n"
).format(date=__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

def log_event(message, log_path=None, level="INFO", section_separator=False):
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    padded_level = f"{level:<5}"
    log_line = f"[{timestamp}] [{padded_level}] | {message}\n"
    
    # Use provided log_path or get from app paths
    if log_path is None:
        paths = get_app_paths()
        log_path = paths.get("out_log", safe_expanduser("~/ClipboardMonitor_output.log"))
    
    _write_log_header_if_needed(log_path, LOG_HEADER)
    with Path(log_path).open('a') as f:
        if section_separator:
            f.write("\n" + "-" * 60 + "\n")
        f.write(log_line)
        if section_separator:
            f.write("-" * 60 + "\n\n")
        f.flush()

def log_error(message, log_path=None, multiline_details=None, section_separator=False):
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    padded_level = "ERROR"
    log_line = f"[{timestamp}] [{padded_level}] | {message}\n"
    
    # Use provided log_path or get from app paths
    if log_path is None:
        paths = get_app_paths()
        log_path = paths.get("err_log", safe_expanduser("~/ClipboardMonitor_error.log"))
    
    _write_log_header_if_needed(log_path, ERR_LOG_HEADER)
    with Path(log_path).open('a') as f:
        if section_separator:
            f.write("\n" + "-" * 60 + "\n")
        f.write(log_line)
        if multiline_details:
            for line in multiline_details.splitlines():
                f.write(f"    {line}\n")
        if section_separator:
            f.write("-" * 60 + "\n\n")
        f.flush()

# Ensure all functions are properly defined at module level
__all__ = [
    'show_notification', 'validate_string_input', 'safe_subprocess_run',
    'get_home_directory', 'safe_expanduser', 'ensure_directory_exists',
    'ContentTracker', 'get_app_paths', 'get_config', 'set_config_value',
    'load_clipboard_history', 'get_clipboard_content', 'update_service_status',
    'get_service_status', 'log_event', 'log_error'
]
