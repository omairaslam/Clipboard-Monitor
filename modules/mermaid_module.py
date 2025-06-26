import subprocess
import webbrowser
import base64
import json
import re
import logging # For logging
from utils import show_notification, log_event, log_error # For centralized notifications
import datetime
import os

MERMAID_PLAYGROUND_BASE = "https://mermaid.live/edit#" # Constants

def is_mermaid_code(text):
    """Check if text contains Mermaid diagram code using regex patterns"""
    if not text or not isinstance(text, str):
        log_event("Content is empty or not a string.", level="DEBUG")
        return False
        
    try:
        # Mermaid diagram patterns
        mermaid_patterns = [
            r"^\s*graph\s",                 # flowchart
            r"^\s*flowchart\b",             # flowchart alternative starter
            r"^\s*sequenceDiagram\b",       # sequence diagram
            r"^\s*classDiagram\b",          # class diagram
            r"^\s*stateDiagram\b",          # state diagram
            r"^\s*erDiagram\b",             # ER diagram
            r"^\s*gantt\b",                 # Gantt chart
            r"^\s*pie\b",                   # Pie chart
            r"^\s*journey\b",               # Journey diagram
            r"^\s*mindmap\b",               # Mindmap
            r"^\s*timeline\b",              # Timeline
            r"^\s*gitGraph\b",              # Git graph
            r"^\s*quadrantChart\b",         # Quadrant chart
            r"^\s*requirementDiagram\b",    # Requirement diagram
            r"^\s*C4Context\b",             # C4 diagrams
            r"^\s*C4Container\b",
            r"^\s*C4Component\b",
            r"^\s*C4Dynamic\b",
        ]
        
        text = text.strip()
        for pattern in mermaid_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                log_event(f"Matched Mermaid pattern: {pattern}", level="DEBUG")
                return True
                
        return False
    except Exception as e:
        log_error(f"Error checking Mermaid code: {str(e)}")
        return False

def create_mermaid_url(mermaid_code):
    """Create Mermaid Live Editor URL using JSON and base64url encoding"""
    try:
        # Create the payload structure
        data = {"code": mermaid_code, "mermaid": {}}
        
        # Convert to JSON with minimal whitespace
        json_str = json.dumps(data, separators=(',', ':'))
        log_event(f"JSON payload: {json_str}", level="DEBUG")
        
        # Encode to base64url
        b64 = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
        log_event(f"Base64 encoded: {b64}", level="DEBUG")
        
        # Create final URL
        url = MERMAID_PLAYGROUND_BASE + b64
        log_event(f"Generated URL: {url}", level="INFO")
        
        return url
    except Exception as e:
        log_error(f"Error creating Mermaid URL: {str(e)}")
        return None

def launch_mermaid_chart(mermaid_code):
    """Launch the Mermaid diagram in browser"""
    try:
        url = create_mermaid_url(mermaid_code)
        if url:
            log_event("Opening Mermaid diagram in browser...", level="INFO")
            webbrowser.open_new(url)
            show_notification("Mermaid Chart", "Opening diagram in Mermaid Live Editor...", "")
            return True
        return False
    except Exception as e:
        log_error(f"Error launching chart: {str(e)}")
        return False

def process(clipboard_content, config=None):
    """Process clipboard content and handle Mermaid diagrams"""
    log_event("Processing clipboard content...", level="DEBUG")
    
    if not clipboard_content:
        return False
        
    try:
        if is_mermaid_code(clipboard_content): # Use centralized notification
            show_notification("Mermaid Detected", "",
                "Processing Mermaid diagram..."
            )
            
            # Sanitize parentheses in node text to prevent Mermaid parsing errors
            sanitized_content = sanitize_mermaid_content(clipboard_content)
            
            # Launch mermaid chart but return False since clipboard isn't modified
            launch_mermaid_chart(sanitized_content)
            return False  # Changed from True to False as clipboard isn't modified
    except Exception as e: # Log error
        log_error(f"Error processing clipboard: {str(e)}")
        
    return False

def sanitize_mermaid_content(mermaid_code):
    """Sanitize Mermaid content to handle problematic characters"""
    try:
        # Pattern to find node text (content inside square brackets, curly braces, or quotes)
        node_text_pattern = r'(\[[^\]]*\]|\{[^}]*\}|"[^"]*")'

        def sanitize_node_text(match):
            text = match.group(0)
            # If it's a bracketed text [like this]
            if text.startswith('[') and text.endswith(']'):
                # Replace parentheses with dashes for better readability
                inner_text = text[1:-1]
                # Replace parentheses with dashes - more readable and Mermaid-compatible
                sanitized_text = inner_text.replace('(', ' - ').replace(')', '')
                # Clean up any double spaces
                sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()
                return f"[{sanitized_text}]"
            # If it's a curly brace text {like this}
            elif text.startswith('{') and text.endswith('}'):
                # Replace parentheses with dashes inside the curly braces
                inner_text = text[1:-1]
                sanitized_text = inner_text.replace('(', ' - ').replace(')', '')
                # Clean up any double spaces
                sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()
                return f"{{{sanitized_text}}}"
            # If it's quoted text "like this"
            elif text.startswith('"') and text.endswith('"'):
                # Replace parentheses with dashes inside the quotes
                inner_text = text[1:-1]
                sanitized_text = inner_text.replace('(', ' - ').replace(')', '')
                # Clean up any double spaces
                sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()
                return f'"{sanitized_text}"'
            return text

        # Replace node text with sanitized version
        sanitized_code = re.sub(node_text_pattern, sanitize_node_text, mermaid_code)

        log_event(f"Original Mermaid content: {mermaid_code}", level="DEBUG")
        log_event(f"Sanitized Mermaid content: {sanitized_code}", level="DEBUG")
        return sanitized_code
    except Exception as e: # Log error
        log_error(f"Error sanitizing Mermaid content: {str(e)}")
        # Return original content if sanitization fails
        return mermaid_code

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

# For testing
if __name__ == '__main__':
    # Test cases including problematic parentheses
    test_cases = [
        """graph TD
        A[Start] --> B{Is it?}
        B -- Yes --> C[OK]
        B -- No --> D[End]""",

        """graph TD
        A[Start (Begin)] --> B{Is it sunny (outside)?}
        B -- Yes (Y) --> C[Go outside (park)]
        B -- No (N) --> D[Stay indoors (home)]
        C --> E[Have fun (enjoy)!]
        D --> E""",

        """sequenceDiagram
        Alice->>John: Hello John, how are you?
        John-->>Alice: Great!""",

        """pie title What Pie Chart
        "Dogs" : 386
        "Cats" : 85
        "Rats" : 15"""
    ]
    
    # Run tests
    log_event("[bold cyan]Running Mermaid module tests...[/bold cyan]", level="INFO")
    for test in test_cases:
        log_event(f"\nTesting with:\n{test}", level="INFO")
        process(test)
