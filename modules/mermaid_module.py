import subprocess
import webbrowser
import base64
import json
import re
import logging # For logging
from pathlib import Path
import pyperclip
try:
    # Try relative import first (when run as module)
    from ..utils import show_notification, log_event, log_error
except ImportError:
    # Fallback for standalone testing
    import sys
    import os
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils import show_notification, log_event, log_error
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

def launch_mermaid_chart(mermaid_code, config=None):
    """Launch the Mermaid diagram in browser and optionally copy URL to clipboard"""
    try:
        url = create_mermaid_url(mermaid_code)
        if not url:
            return False

        log_event("Opening Mermaid diagram in browser...", level="INFO")
        webbrowser.open_new(url)
        show_notification("Mermaid Chart", "Opening diagram in Mermaid Live Editor...", "")

        if config and config.get('mermaid_copy_url', False):
            pyperclip.copy(url)
            show_notification("Mermaid URL Copied", "The encoded URL has been copied to the clipboard.", "")
            return True  # Clipboard was modified

        return False  # Clipboard was not modified
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
            # Launch mermaid chart and check if clipboard was modified
            return launch_mermaid_chart(sanitized_content, config)
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
