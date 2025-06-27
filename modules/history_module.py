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

try:
    # Try relative import first (when run as module)
    from ..utils import validate_string_input, ContentTracker, safe_expanduser, ensure_directory_exists, log_event, log_error
    from ..config_manager import ConfigManager
    from ..lock_manager import LockManager
    from ..constants import DEFAULT_HISTORY_CONFIG, CONTENT_TRACKER_MAX_HISTORY
except ImportError:
    # Fallback to adding parent directory to path (for standalone testing)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils import validate_string_input, ContentTracker, safe_expanduser, ensure_directory_exists, log_event, log_error
    from config_manager import ConfigManager
    from lock_manager import LockManager
    from constants import DEFAULT_HISTORY_CONFIG, CONTENT_TRACKER_MAX_HISTORY

logger = logging.getLogger("history_module")

# Global content tracker to prevent processing loops
_content_tracker = ContentTracker(max_history=CONTENT_TRACKER_MAX_HISTORY)
_lock_manager = LockManager()

def get_history_config():
    """Get history configuration from the main config.json."""
    config_manager = ConfigManager()
    return config_manager.get_section('history', DEFAULT_HISTORY_CONFIG)

def get_history_path():
    """Get the path to the history file"""
    config = get_history_config()
    path = config.get('save_location', DEFAULT_HISTORY_CONFIG['save_location'])
    return safe_expanduser(path)

def load_history():
    """Load clipboard history from file"""
    history_path = Path(get_history_path())
    
    try:
        # Create directory if it doesn't exist
        ensure_directory_exists(str(history_path.parent))
        
        # Load history if file exists
        if history_path.exists():
            with history_path.open('r') as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Error loading history: {e}")
        log_error(f"Error loading history: {e}")  # Log using improved logger
    
    return []

def save_history(history):
    """Save clipboard history to file"""
    history_path = Path(get_history_path())
    
    try:
        # Create directory if it doesn't exist
        ensure_directory_exists(str(history_path.parent))
        
        # Save history
        with history_path.open('w') as f:
            json.dump(history, f, indent=2)
    except (OSError, json.JSONEncodeError) as e:
        logger.error(f"Error saving history: {e}")
        log_error(f"Error saving history: {e}")  # Log using improved logger

def add_to_history(content):
    """Add content to clipboard history"""
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
    save_history(history)

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

def _write_log_header_if_needed(log_path, header):
    """Write a header to the log file if it is empty."""
    log_file = Path(log_path)
    if not log_file.exists() or log_file.stat().st_size == 0:
        with log_file.open('a') as f:
            f.write(header)

LOG_HEADER = (
    f"=== Clipboard Monitor Output Log ===\n"
    f"Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    f"Format: [YYYY-MM-DD HH:MM:SS] [LEVEL ] | Message\n"
    f"-------------------------------------\n"
)

ERR_LOG_HEADER = (
    f"=== Clipboard Monitor Error Log ===\n"
    f"Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    f"Format: [YYYY-MM-DD HH:MM:SS] [LEVEL ] | Message\n"
    f"-------------------------------------\n"
)

def log_event(message, level="INFO", section_separator=False, paths=None):
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    padded_level = f"{level:<5}"
    log_line = f"[{timestamp}] [{padded_level}] | {message}\n"
    # Use get_app_paths if available, else fallback
    if paths is not None:
        out_log = paths.get("out_log")
    else:
        try:
            from utils import get_app_paths, safe_expanduser
            out_log = get_app_paths().get("out_log", safe_expanduser("~/ClipboardMonitor_output.log"))
        except Exception:
            out_log = safe_expanduser("~/ClipboardMonitor_output.log")
    _write_log_header_if_needed(out_log, LOG_HEADER)
    with Path(out_log).open('a') as f:
        if section_separator:
            f.write("\n" + "-" * 60 + "\n")
        f.write(log_line)
        if section_separator:
            f.write("-" * 60 + "\n\n")
        f.flush()

def log_error(message, multiline_details=None, section_separator=False, paths=None):
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    padded_level = f"ERROR"
    log_line = f"[{timestamp}] [{padded_level}] | {message}\n"
    # Use get_app_paths if available, else fallback
    if paths is not None:
        err_log = paths.get("err_log")
    else:
        try:
            from utils import get_app_paths, safe_expanduser
            err_log = get_app_paths().get("err_log", safe_expanduser("~/ClipboardMonitor_error.log"))
        except Exception:
            err_log = safe_expanduser("~/ClipboardMonitor_error.log")
    _write_log_header_if_needed(err_log, ERR_LOG_HEADER)
    with Path(err_log).open('a') as f:
        if section_separator:
            f.write("\n" + "-" * 60 + "\n")
        f.write(log_line)
        if multiline_details:
            for line in multiline_details.splitlines():
                f.write(f"    {line}\n")
        if section_separator:
            f.write("-" * 60 + "\n\n")
        f.flush()

# Replace all logger.info, logger.warning, logger.error, logger.debug calls with log_event or log_error as appropriate
