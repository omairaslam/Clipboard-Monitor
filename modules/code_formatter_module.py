import subprocess
import pyperclip
import logging
import re
import threading
import sys
import os
import json
import datetime

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # For utils
from utils import show_notification, validate_string_input, ContentTracker, get_config, log_event, log_error

logger = logging.getLogger("code_formatter_module")

# Global content tracker to prevent processing loops
_content_tracker = ContentTracker(max_history=5)
_processing_lock = threading.Lock()

def is_code(text):
    """Detect if text is likely code"""
    # Simple heuristics for code detection
    code_patterns = [
        r'^\s*(def|class|import|from|if|for|while|try|except|with)\s+',  # Python
        r'^\s*(function|const|let|var|import|export|class|interface|if|for|while|try|catch)\s+',  # JavaScript/TypeScript
        r'^\s*(public|private|protected|class|interface|enum|void|int|string|boolean)\s+',  # Java/C#
        r'^\s*(func|struct|import|var|let|if|for|while|switch|guard)\s+',  # Swift/Go
    ]
    
    lines = text.split('\n')
    code_lines = 0
    
    for line in lines:
        if any(re.search(pattern, line) for pattern in code_patterns):
            code_lines += 1
    
    # If at least 15% of lines match code patterns and there are at least 3 lines
    return len(lines) >= 3 and (code_lines / len(lines) >= 0.15)

def format_code(code_text):
    """Format code using black for Python, prettier for JS/TS, etc."""
    # Try to detect language
    if re.search(r'^\s*(def|class|import|from)\s+', code_text, re.MULTILINE):
        # Python code - use black
        try:
            process = subprocess.Popen(
                ['black', '-', '-q'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(input=code_text.encode('utf-8'), timeout=5)
            if process.returncode == 0:
                return stdout.decode('utf-8')
            else:
                log_event(f"Black formatting failed: {stderr.decode('utf-8')}", level="WARNING")
                return code_text
        except Exception as e:
            log_error(f"Error formatting Python code: {e}")
            return code_text
    
    # Add more language formatters as needed
    
    return code_text  # Return original if no formatter matched

def process(clipboard_content, config=None):
    """Process clipboard content if it appears to be code"""
    # Prevent concurrent processing and loops
    with _processing_lock:
        # Safety check for None or empty content
        if not validate_string_input(clipboard_content, "clipboard_content"):
            return False

        # Prevent processing the same content repeatedly
        if _content_tracker.has_processed(clipboard_content):
            logger.debug("Skipping code formatting - content already processed recently")
            return False

        if is_code(clipboard_content):
            log_event("Code detected!")

            # Check if clipboard modification is enabled for this module
            # Use module_config passed from main, or load if not provided (for standalone testing)
            modify_clipboard = (config or get_config('modules')).get('code_formatter_modify_clipboard', False)

            # Track this content to prevent reprocessing
            _content_tracker.add_content(clipboard_content)

            if modify_clipboard:
                # Only format and modify clipboard if explicitly enabled
                show_notification("Code Detected", "Formatting code...", "")
                formatted_code = format_code(clipboard_content)
                if formatted_code != clipboard_content: # Use centralized notification
                    try:
                        # Copy formatted code back to clipboard
                        pyperclip.copy(formatted_code)

                        log_event("Code formatted and copied to clipboard!")
                        show_notification("Code Formatted", "Formatted code copied to clipboard!", "")
                        return True
                    except Exception as e:
                        log_error(f"Error copying formatted code: {e}")
                else:
                    log_event("Code already properly formatted")
            else:
                # Read-only mode: just notify about code detection
                show_notification("Code Detected", "Code detected (read-only mode)", "")
                logger.info("[blue]Code detected but clipboard modification disabled for safety[/blue]")
                return False  # Don't modify clipboard
                
    return False

def _write_log_header_if_needed(log_path, header):
    """Write a header to the log file if it is empty."""
    if not os.path.exists(log_path) or os.path.getsize(log_path) == 0:
        with open(log_path, 'a') as f:
            f.write(header)

LOG_HEADER = (
    "=== Clipboard Monitor Output Log ===\n"
    "Created: {date}\n"
    "Format: [YYYY-MM-DD HH:MM:SS] [LEVEL ] | Message\n"
    "-------------------------------------\n"
).format(date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

ERR_LOG_HEADER = (
    "=== Clipboard Monitor Error Log ===\n"
    "Created: {date}\n"
    "Format: [YYYY-MM-DD HH:MM:SS] [LEVEL ] | Message\n"
    "-------------------------------------\n"
).format(date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

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
            from utils import get_app_paths
            out_log = get_app_paths().get("out_log", os.path.expanduser("~/ClipboardMonitor_output.log"))
        except Exception:
            out_log = os.path.expanduser("~/ClipboardMonitor_output.log")
    _write_log_header_if_needed(out_log, LOG_HEADER)
    with open(out_log, 'a') as f:
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
            from utils import get_app_paths
            err_log = get_app_paths().get("err_log", os.path.expanduser("~/ClipboardMonitor_error.log"))
        except Exception:
            err_log = os.path.expanduser("~/ClipboardMonitor_error.log")
    _write_log_header_if_needed(err_log, ERR_LOG_HEADER)
    with open(err_log, 'a') as f:
        if section_separator:
            f.write("\n" + "-" * 60 + "\n")
        f.write(log_line)
        if multiline_details:
            for line in multiline_details.splitlines():
                f.write(f"    {line}\n")
        if section_separator:
            f.write("-" * 60 + "\n\n")
        f.flush()