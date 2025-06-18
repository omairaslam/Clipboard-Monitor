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
from rich.console import Console

# Set up rich console
console = Console()
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
