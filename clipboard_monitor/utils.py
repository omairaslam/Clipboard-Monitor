"""
Shared utilities for the clipboard monitor application.
"""
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def show_notification(title: str, message: str) -> None:
    """
    Displays a macOS notification using AppleScript with proper error handling.
    
    Args:
        title: The notification title
        message: The notification message
    """
    try:
        # Escape quotes to prevent AppleScript injection
        safe_title = title.replace('"', '\\"').replace("'", "\\'")
        safe_message = message.replace('"', '\\"').replace("'", "\\'")
        
        script = f'display notification "{safe_message}" with title "{safe_title}"'
        
        result = subprocess.run(
            ['osascript', '-e', script],
            check=False,
            timeout=5,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0 and result.stderr:
            logger.warning(f"AppleScript warning: {result.stderr.strip()}")
            
    except subprocess.TimeoutExpired:
        logger.warning("Notification timeout - AppleScript took too long")
    except FileNotFoundError:
        logger.error("osascript not found - notifications not available")
    except Exception as e:
        logger.error(f"Error showing notification: {e}")

def validate_string_input(value, name: str = "input") -> bool:
    """
    Validate that a value is a non-empty string.
    
    Args:
        value: The value to validate
        name: Name of the value for error messages
        
    Returns:
        True if valid, False otherwise
    """
    if value is None:
        logger.debug(f"{name} is None")
        return False
        
    if not isinstance(value, str):
        logger.debug(f"{name} is not a string: {type(value)}")
        return False
        
    if not value.strip():
        logger.debug(f"{name} is empty or whitespace-only")
        return False
        
    return True

def safe_subprocess_run(cmd: list, timeout: int = 30, **kwargs) -> Optional[subprocess.CompletedProcess]:
    """
    Safely run a subprocess with timeout and error handling.
    
    Args:
        cmd: Command to run as a list
        timeout: Timeout in seconds
        **kwargs: Additional arguments for subprocess.run
        
    Returns:
        CompletedProcess object or None if failed
    """
    try:
        return subprocess.run(
            cmd,
            timeout=timeout,
            check=False,
            **kwargs
        )
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        return None
    except FileNotFoundError:
        logger.error(f"Command not found: {cmd[0]}")
        return None
    except Exception as e:
        logger.error(f"Error running command {' '.join(cmd)}: {e}")
        return None

class ContentTracker:
    """
    Utility class to track processed content and prevent loops.
    """
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history = []
        
    def add_content(self, content: str) -> None:
        """Add content to the history."""
        content_hash = self._hash_content(content)
        
        # Remove if already exists
        if content_hash in self.history:
            self.history.remove(content_hash)
            
        # Add to front
        self.history.insert(0, content_hash)
        
        # Trim to max size
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
    
    def has_processed(self, content: str) -> bool:
        """Check if content has been processed recently."""
        content_hash = self._hash_content(content)
        return content_hash in self.history
    
    def _hash_content(self, content: str) -> str:
        """Generate a hash of the content."""
        import hashlib
        if content is None:
            return "none"
        return hashlib.md5(str(content).encode()).hexdigest()[:16]  # Short hash
    
    def clear(self) -> None:
        """Clear the history."""
        self.history.clear()
