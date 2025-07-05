"""
ClipboardReader class - Handles all clipboard access operations.
Extracted from main.py for better modularity and testability.
"""

import logging
from utils import get_clipboard_content

logger = logging.getLogger("clipboard_reader")


class ClipboardReader:
    """
    Handles clipboard reading operations with caching and change detection.
    """
    def __init__(self, content_tracker=None):
        """Initialize the clipboard reader.
        Args:
            content_tracker (ContentTracker, optional): Tracker for deduplication. If None, disables tracking.
        """
        self.last_content = None
        self.last_content_hash = None
        self.content_tracker = content_tracker
    
    def get_changed_clipboard_content(self):
        """
        Alias for get_content_if_changed() for backward compatibility with tests.
        Returns:
            str or None: New clipboard content if changed, None if unchanged or error
        """
        if hasattr(self, 'is_paused') and self.is_paused:
            return None
        return self.get_content_if_changed()

    def get_content(self):
        """
        Get current clipboard content using centralized utility function.
        
        Returns:
            str or None: Current clipboard content, or None if no content/error
        """
        return get_clipboard_content()
    
    def has_content_changed(self, current_content=None):
        """
        Check if clipboard content has changed since last check.
        Args:
            current_content (str, optional): Current clipboard content. 
                                           If None, will fetch current content.
        Returns:
            bool: True if content has changed, False otherwise
        """
        changed = False
        if current_content is None:
            current_content = self.get_content()
        if self.content_tracker:
            if not self.content_tracker.has_processed(current_content):
                self.content_tracker.add_content(current_content)
                self.last_content = current_content
                changed = True
            else:
                changed = False
        elif current_content != self.last_content:
            self.last_content = current_content
            changed = True
        else:
            changed = False
        return changed
    
    def get_content_if_changed(self):
        """
        Get clipboard content only if it has changed since last check.
        Returns:
            str or None: New clipboard content if changed, None if unchanged or error
        """
        current_content = self.get_content()
        result = None
        if hasattr(self, 'is_paused') and self.is_paused:
            result = None
        elif self.has_content_changed(current_content):
            result = current_content
        else:
            result = None
        return result
    
    def reset_tracking(self):
        """Reset content tracking to force next check to return content."""
        self.last_content = None
        self.last_content_hash = None