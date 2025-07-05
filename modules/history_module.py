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
import datetime
import tempfile
import shutil
try:
    import fcntl  # Unix only
except ImportError:
    fcntl = None

try:
    # Try absolute import first (for normal execution and testing)
    from utils import validate_string_input, ContentTracker, safe_expanduser, ensure_directory_exists, log_event, log_error
    from config_manager import ConfigManager
    from lock_manager import LockManager
    from constants import DEFAULT_HISTORY_CONFIG, CONTENT_TRACKER_MAX_HISTORY
except ImportError:
    # Fallback to relative import (for package/module execution)
    from ..utils import validate_string_input, ContentTracker, safe_expanduser, ensure_directory_exists, log_event, log_error
    from ..config_manager import ConfigManager
    from ..lock_manager import LockManager
    from ..constants import DEFAULT_HISTORY_CONFIG, CONTENT_TRACKER_MAX_HISTORY

logger = logging.getLogger("history_module")

# Global content tracker to prevent processing loops
_content_tracker = ContentTracker(max_history=CONTENT_TRACKER_MAX_HISTORY)
_lock_manager = LockManager() # Used by process()
_add_to_history_lock = threading.Lock() # For add_to_history internal thread safety

def get_history_config():
    """Get history configuration from the main config.json."""
    config_manager = ConfigManager()
    return config_manager.get_section('history', DEFAULT_HISTORY_CONFIG)

def get_history_path():
    """Get the path to the history file"""
    config = get_history_config()
    path = config.get('save_location', DEFAULT_HISTORY_CONFIG['save_location'])
    return safe_expanduser(path)

def _acquire_file_lock(f):
    if fcntl:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        except Exception as e: # Log if lock acquisition fails
            logger.warning(f"Failed to acquire file lock on {f.name if hasattr(f, 'name') else 'fd:'+str(f.fileno())}: {e}")
            pass # Continue without lock

def _release_file_lock(f):
    if fcntl:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e: # Log if lock release fails
            logger.warning(f"Failed to release file lock on {f.name if hasattr(f, 'name') else 'fd:'+str(f.fileno())}: {e}")
            pass

def load_history():
    """Load clipboard history from file, with file lock and corruption recovery."""
    history_path = Path(get_history_path())
    try:
        ensure_directory_exists(str(history_path.parent))
        if not history_path.exists():
            return []

        # Try to read and parse
        try:
            with history_path.open('r') as f:
                _acquire_file_lock(f)
                try:
                    data = json.load(f)
                    return data # Lock released in finally
                finally:
                    _release_file_lock(f)
        except json.JSONDecodeError:
            logger.warning(f"History file {history_path} is corrupted. Attempting backup and reset.")
            backup_path = history_path.with_suffix('.corrupt.bak')
            try:
                shutil.copy(str(history_path), str(backup_path))
                logger.info(f"Backed up corrupted history to {backup_path}")
            except Exception as backup_e:
                logger.error(f"Failed to create backup of corrupted history {history_path}: {type(backup_e).__name__} - {backup_e}")
                # Removed re-raise. If shutil.copy fails, this log is the main indicator.

            # Reset the history file by writing an empty list
            try:
                with history_path.open('w') as f_write: # Open in write mode to truncate/overwrite
                    _acquire_file_lock(f_write) # Lock for writing
                    try:
                        json.dump([], f_write)
                    finally:
                        _release_file_lock(f_write)
                logger.info(f"Reset corrupted history file {history_path} to empty list.")
            except Exception as reset_e:
                logger.error(f"Failed to reset corrupted history file {history_path}: {reset_e}")
            return [] # Return empty list after corruption detected
        except OSError as e: # Catch OS errors from initial file open/read attempts
            logger.error(f"OSError while reading history file {history_path}: {e}")
            log_error(f"OSError while reading history file {history_path}: {e}")
            return []

    except Exception as outer_e: # Catch errors from get_history_path or ensure_directory_exists
        logger.error(f"Unexpected error during history load setup: {outer_e}")
        log_error(f"Unexpected error during history load setup: {outer_e}")
    return []

def save_history(history):
    """Save clipboard history to file atomically with file lock."""
    history_path = Path(get_history_path())
    try:
        ensure_directory_exists(str(history_path.parent))
        # Write to a temp file first
        with tempfile.NamedTemporaryFile('w', dir=str(history_path.parent), delete=False) as tf:
            _acquire_file_lock(tf)
            json.dump(history, tf, indent=2)
            tf.flush()
            os.fsync(tf.fileno())
            _release_file_lock(tf)
            temp_path = Path(tf.name)
        # Atomically replace the original file
        temp_path.replace(history_path)
    except (OSError, json.JSONEncodeError) as e:
        logger.error(f"Error saving history: {e}")
        log_error(f"Error saving history: {e}")

def add_to_history(content):
    """Add content to clipboard history"""
    with _add_to_history_lock: # Protect the entire read-modify-write operation
        if not content:
            return

        config = get_history_config()
    max_items = config.get('max_items', DEFAULT_HISTORY_CONFIG['max_items'])
    max_content_length = config.get('max_content_length', DEFAULT_HISTORY_CONFIG['max_content_length'])
    
    # Truncate content if needed
    if len(content) > max_content_length:
        content = f"{content[:max_content_length]}... (truncated)"
    
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
    save_history(history) # This is now inside the `with _add_to_history_lock` block

def process(clipboard_content, config=None):
    """Process clipboard content by adding it to history"""
    
    # Prevent concurrent processing and loops
    with _lock_manager.get_clipboard_processing_lock():
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
        except (OSError, json.JSONDecodeError, json.JSONEncodeError) as e:
            logger.error(f"Error adding to history: {e}")
            log_error(f"Error adding to history: {e}")  # Log using improved logger
            return False

def reset_content_tracker():
    """Reset the in-memory content tracker (for test isolation)."""
    global _content_tracker
    _content_tracker = ContentTracker(max_history=CONTENT_TRACKER_MAX_HISTORY)

# --- History Clearing Function ---
def clear_history():
    """Clear the clipboard history file and reset in-memory tracker."""
    history_path = Path(get_history_path())
    try:
        ensure_directory_exists(str(history_path.parent))
        # Overwrite the file with an empty list atomically
        with tempfile.NamedTemporaryFile('w', dir=str(history_path.parent), delete=False) as tf:
            _acquire_file_lock(tf)
            json.dump([], tf, indent=2)
            tf.flush()
            os.fsync(tf.fileno())
            _release_file_lock(tf)
            temp_path = Path(tf.name)
        temp_path.replace(history_path)
        # Reset in-memory content tracker
        global _content_tracker
        _content_tracker.clear() # Call clear method instead of re-assigning
        log_event("Clipboard history cleared.")
        return True
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        log_error(f"Error clearing history: {e}")
        return False
