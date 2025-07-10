import subprocess
import webbrowser
import base64
import json
import re
import logging
from pathlib import Path
import pyperclip
import sys
import os
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import show_notification, log_event, log_error

MERMAID_PLAYGROUND_BASE = "https://mermaid.live/edit#"

def is_mermaid_code(text):
    """Check if text contains Mermaid diagram code using regex patterns"""
    if not text or not isinstance(text, str):
        log_event("Content is empty or not a string.", level="DEBUG")
        return False
        
    try:
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

def create_mermaid_url(mermaid_code, theme="default"):
    """Create Mermaid Live Editor URL using JSON and base64url encoding, including theme."""
    try:
        mermaid_config = {}
        if theme and theme.lower() != "default":
            mermaid_config["theme"] = theme

        data = {"code": mermaid_code, "mermaid": mermaid_config}
        
        json_str = json.dumps(data, separators=(',', ':'))
        b64 = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
        return f"{MERMAID_PLAYGROUND_BASE}{b64}"
    except Exception as e:
        log_error(f"Error creating Mermaid URL: {str(e)}")
        return None

def launch_mermaid_chart(mermaid_code, config=None):
    """Launch Mermaid diagram in browser and handle clipboard content"""
    try:
        mermaid_theme = config.get('mermaid_theme', "default") if config else "default"
        url = create_mermaid_url(mermaid_code, theme=mermaid_theme)
        if not url:
            return None

        open_browser = config.get('mermaid_open_in_browser', True) if config else True
        copy_code = config.get('mermaid_copy_code', True) if config else True
        copy_url = config.get('mermaid_copy_url', False) if config else False

        # Handle clipboard copying in the requested order: code first, then URL
        clipboard_content = None
        if copy_code and copy_url:
            # First copy the code
            pyperclip.copy(mermaid_code)
            log_event("Copied Mermaid code to clipboard", level="INFO")
            show_notification("Mermaid Code", "Diagram code copied to clipboard", "")

            # Then copy the URL
            pyperclip.copy(url)
            log_event("Copied Mermaid URL to clipboard", level="INFO")
            show_notification("Mermaid URL", "URL copied to clipboard", "")
            clipboard_content = url  # Return URL as final clipboard content
        elif copy_code:
            clipboard_content = mermaid_code
            show_notification("Mermaid Code", "Diagram code copied to clipboard", "")
        elif copy_url:
            clipboard_content = url
            show_notification("Mermaid URL", "URL copied to clipboard", "")

        # Open browser after clipboard operations
        if open_browser:
            webbrowser.open_new(url)
            log_event("Opened Mermaid diagram in browser", level="INFO")

        return clipboard_content

    except Exception as e:
        log_error(f"Error launching chart: {str(e)}")
        return None

def process(clipboard_content, config=None):
    """Process clipboard content and handle Mermaid diagrams"""
    log_event("Processing clipboard content...", level="DEBUG")
    
    if not clipboard_content:
        return None
        
    try:
        if is_mermaid_code(clipboard_content):
            show_notification("Mermaid Detected", "", "Processing Mermaid diagram...")
            sanitized_content = sanitize_mermaid_content(clipboard_content)
            return launch_mermaid_chart(sanitized_content, config)
    except Exception as e:
        log_error(f"Error processing clipboard: {str(e)}")
        
    return None

def sanitize_mermaid_content(mermaid_code):
    """Sanitize Mermaid content to handle problematic characters"""
    try:
        node_text_pattern = r'(\[[^\]]*\]|\{[^}]*\}|"[^"]*")'

        def sanitize_node_text(match):
            text = match.group(0)
            if text.startswith('[') and text.endswith(']'):
                inner_text = text[1:-1].replace('(', ' - ').replace(')', '')
                return f"[{inner_text.strip()}]"
            elif text.startswith('{') and text.endswith('}'):
                inner_text = text[1:-1].replace('(', ' - ').replace(')', '')
                return f"{{{inner_text.strip()}}}"
            elif text.startswith('"') and text.endswith('"'):
                inner_text = text[1:-1].replace('(', ' - ').replace(')', '')
                return f'"{inner_text.strip()}"'
            return text

        return re.sub(node_text_pattern, sanitize_node_text, mermaid_code)
    except Exception as e:
        log_error(f"Error sanitizing Mermaid content: {str(e)}")
        return mermaid_code
