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

def show_notification(title, message):
    """
    Show a notification using AppleScript (macOS).
    
    Args:
        title (str): The notification title
        message (str): The notification message
    """
    try:
        # Sanitize inputs to prevent AppleScript injection
        title = validate_string_input(title, "title", default="Notification")
        message = validate_string_input(message, "message", default="")
        
        # Escape quotes to prevent AppleScript injection
        title = title.replace('"', '\\"')
        message = message.replace('"', '\\"')
        
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

    # If all methods fail, raise an error
    raise RuntimeError("Unable to determine user home directory using any method")

def safe_expanduser(path):
    """
    Safely expand user home directory in paths, with robust fallback methods.
    This prevents the creation of literal ~ folders when working directory
    is set incorrectly.

    Args:
        path (str): Path that may contain ~ for home directory

    Returns:
        str: Path with ~ properly expanded to home directory

    Raises:
        RuntimeError: If home directory cannot be determined
    """
    if not isinstance(path, str):
        raise ValueError("Path must be a string")

    # If path doesn't start with ~, return as-is
    if not path.startswith("~"):
        return path

    try:
        # Get the home directory using our robust method
        home_dir = get_home_directory()

        # Handle different tilde patterns
        if path == "~":
            return home_dir
        elif path.startswith("~/"):
            return os.path.join(home_dir, path[2:])
        elif path.startswith("~"):
            # Handle ~username patterns (though less common)
            return os.path.expanduser(path)
        else:
            return path

    except Exception as e:
        logger.error(f"Failed to expand path '{path}': {e}")
        raise RuntimeError(f"Unable to expand user path: {path}")

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
    """Return standardized application paths"""
    base_dir = safe_expanduser("~/Library/Application Support/ClipboardMonitor")
    return {
        "base_dir": base_dir,
        "history_file": os.path.join(base_dir, "clipboard_history.json"),
        "pause_flag": os.path.join(base_dir, "pause_flag"),
        "error_log": os.path.join(base_dir, "error.log"),
        "status_file": os.path.join(base_dir, "status.txt")
    }

def get_config(section=None, key=None, default=None):
    """Get configuration value from config.json
    
    Args:
        section: Optional section name (e.g., 'general', 'modules')
        key: Optional key within section
        default: Default value if section/key not found
        
    Returns:
        Full config dict, section dict, or specific value
    """
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            if section is None:
                return config
            elif section in config:
                if key is None:
                    return config[section]
                else:
                    return config[section].get(key, default)
        return default
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return default

def set_config_value(section, key, value):
    """Set a configuration value in config.json"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')

        # Load existing config
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}

        # Ensure section exists
        if section not in config:
            config[section] = {}

        # Set the value
        config[section][key] = value

        # Save back to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        return True
    except Exception as e:
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
        history_path = safe_expanduser(history_path_str)

        if os.path.exists(history_path):
            with open(history_path, 'r') as f:
                history = json.load(f)
                return history
        return []
    except Exception as e:
        logger.error(f"Error loading clipboard history from {history_path}: {e}")
        return []

def get_clipboard_content():
    """Get clipboard content with fallback mechanisms.
    
    Returns:
        String content of clipboard or None if retrieval fails
    """
    try:
        # Try pbpaste first (macOS)
        try:
            # Try RTF first
            result = subprocess.run(
                ['pbpaste', '-Prefer', 'rtf'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
                
            # Try plain text
            result = subprocess.run(
                ['pbpaste', '-Prefer', 'txt'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
            
        # Fall back to pyperclip
        return pyperclip.paste()
    except Exception as e:
        logging.error(f"Error getting clipboard content: {e}")
        return None

def update_service_status(status):
    """Update the service status file
    
    Args:
        status: String status ('running_enhanced', 'running_polling', 'paused', 'error')
    """
    try:
        paths = get_app_paths()
        ensure_directory_exists(os.path.dirname(paths["status_file"]))
        with open(paths["status_file"], 'w') as f:
            f.write(status)
    except Exception as e:
        logging.error(f"Error updating status file: {e}")

def get_service_status():
    """Get current service status from status file
    
    Returns:
        String status or 'unknown' if status file doesn't exist/can't be read
    """
    try:
        paths = get_app_paths()
        if os.path.exists(paths["status_file"]):
            with open(paths["status_file"], 'r') as f:
                return f.read().strip()
        return "unknown"
    except Exception:
        return "unknown"

# Ensure all functions are properly defined at module level
__all__ = [
    'show_notification', 'validate_string_input', 'safe_subprocess_run',
    'get_home_directory', 'safe_expanduser', 'ensure_directory_exists',
    'ContentTracker', 'get_app_paths', 'get_config', 'set_config_value',
    'load_clipboard_history', 'get_clipboard_content', 'update_service_status',
    'get_service_status'
]
