"""
Clipboard History Module
Tracks clipboard history with timestamps and content hashing for deduplication.
"""

import os
import json
import time
import hashlib
import threading
from pathlib import Path
import sys
import logging

# Add parent directory to path to import utils (for get_config)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
from utils import validate_string_input, ContentTracker, safe_expanduser, ensure_directory_exists, get_config

logger = logging.getLogger("history_module")

# Global content tracker to prevent processing loops
_content_tracker = ContentTracker(max_history=5)
_processing_lock = threading.Lock()

# Default configuration
DEFAULT_CONFIG = {
    "max_items": 100,
    "max_content_length": 10000,
    "save_location": "~/Library/Application Support/ClipboardMonitor/clipboard_history.json"
}

def get_history_config():
    """Get history configuration from the main config.json."""
    return get_config('history', default=DEFAULT_CONFIG)

def get_history_path():
    """Get the path to the history file"""
    config = get_history_config()
    path = config.get('save_location', DEFAULT_CONFIG['save_location'])
    return safe_expanduser(path)

def load_history():
    """Load clipboard history from file"""
    history_path = get_history_path()
    
    try:
        # Create directory if it doesn't exist
        ensure_directory_exists(os.path.dirname(history_path))
        
        # Load history if file exists
        if os.path.exists(history_path):
            with open(history_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading history: {e}")
    
    return []

def save_history(history):
    """Save clipboard history to file"""
    history_path = get_history_path()
    
    try:
        # Create directory if it doesn't exist
        ensure_directory_exists(os.path.dirname(history_path))
        
        # Save history
        with open(history_path, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving history: {e}")

def add_to_history(content):
    """Add content to clipboard history"""
    if not content:
        return

    config = get_history_config()
    max_items = config.get('max_items', DEFAULT_CONFIG['max_items'])
    max_content_length = config.get('max_content_length', DEFAULT_CONFIG['max_content_length'])
    
    # Truncate content if needed
    if len(content) > max_content_length:
        content = content[:max_content_length] + "... (truncated)"
    
    # Create history item
    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    history_item = {
        'timestamp': time.time(),
        'content': content,
        'hash': content_hash
    }
    
    # Load existing history
    history = load_history()
    
    # Check for duplicates (by hash)
    for item in history:
        if item.get('hash') == content_hash:
            # Move to top of history (most recent)
            history.remove(item)
            item['timestamp'] = time.time()  # Update timestamp
            history.insert(0, item)
            save_history(history)
            return
    
    # Add new item to the beginning
    history.insert(0, history_item)
    
    # Trim history if needed
    if len(history) > max_items:
        history = history[:max_items]
    
    # Save updated history
    save_history(history)

def process(clipboard_content, module_config=None) -> bool:
    """Process clipboard content by adding it to history"""
    
    # Prevent concurrent processing and loops
    with _processing_lock:
        # Safety check for None or empty content
        if not validate_string_input(clipboard_content, "clipboard_content"):
            return False

        # Prevent processing the same content repeatedly
        if _content_tracker.has_processed(clipboard_content):
            logger.debug("Skipping history tracking - content already processed recently")
            return False
        
        try:
            # Track this content to prevent reprocessing
            _content_tracker.add_content(clipboard_content)
            
            # Add to history
            add_to_history(clipboard_content)
            
            # This module doesn't modify the clipboard, so return False
            # to allow other modules to process the content
            return False
        except Exception as e:
            logger.error(f"Error adding to history: {e}")
            return False
