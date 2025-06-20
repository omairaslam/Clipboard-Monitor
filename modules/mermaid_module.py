import subprocess
import webbrowser
import base64
import json
import re
from rich.console import Console
from rich.logging import RichHandler
import logging

# Constants
MERMAID_PLAYGROUND_BASE = "https://mermaid.live/edit#"

# Set up rich logging
console = Console()
logger = logging.getLogger("mermaid_module")

def show_notification(title, message):
    """Show a notification using AppleScript (macOS)"""
    try:
        logger.debug(f"Attempting to show notification: {title} - {message}")
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}"'
        ])
        logger.debug("Notification shown successfully.")
    except Exception as e:
        logger.error(f"[bold red]Notification error:[/bold red] {str(e)}")

def is_mermaid_code(text):
    """Check if text contains Mermaid diagram code using regex patterns"""
    if not text or not isinstance(text, str):
        logger.debug("Content is empty or not a string.")
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
                logger.debug(f"Matched Mermaid pattern: {pattern}")
                return True
                
        return False
    except Exception as e:
        logger.error(f"[bold red]Error checking Mermaid code:[/bold red] {str(e)}")
        return False

def create_mermaid_url(mermaid_code):
    """Create Mermaid Live Editor URL using JSON and base64url encoding"""
    try:
        # Create the payload structure
        data = {"code": mermaid_code, "mermaid": {}}
        
        # Convert to JSON with minimal whitespace
        json_str = json.dumps(data, separators=(',', ':'))
        logger.debug(f"JSON payload: {json_str}")
        
        # Encode to base64url
        b64 = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
        logger.debug(f"Base64 encoded: {b64}")
        
        # Create final URL
        url = MERMAID_PLAYGROUND_BASE + b64
        logger.info(f"[blue]Generated URL:[/blue] {url}")
        
        return url
    except Exception as e:
        logger.error(f"[bold red]Error creating Mermaid URL:[/bold red] {str(e)}")
        return None

def launch_mermaid_chart(mermaid_code):
    """Launch the Mermaid diagram in browser"""
    try:
        url = create_mermaid_url(mermaid_code)
        if url:
            logger.info("[green]Opening Mermaid diagram in browser...[/green]")
            webbrowser.open_new(url)
            show_notification(
                "Mermaid Chart", 
                "Opening diagram in Mermaid Live Editor..."
            )
            return True
        return False
    except Exception as e:
        logger.error(f"[bold red]Error launching chart:[/bold red] {str(e)}")
        return False

def process(clipboard_content):
    """Process clipboard content and handle Mermaid diagrams"""
    logger.debug("Processing clipboard content...")
    
    if not clipboard_content:
        return False
        
    try:
        if is_mermaid_code(clipboard_content):
            logger.info("[cyan]Mermaid diagram detected![/cyan]")
            show_notification(
                "Mermaid Detected",
                "Processing Mermaid diagram..."
            )
            
            # Sanitize parentheses in node text to prevent Mermaid parsing errors
            sanitized_content = sanitize_mermaid_content(clipboard_content)
            
            # Launch mermaid chart but return False since clipboard isn't modified
            launch_mermaid_chart(sanitized_content)
            return False  # Changed from True to False as clipboard isn't modified
    except Exception as e:
        logger.error(f"[bold red]Error processing clipboard:[/bold red] {str(e)}")
        
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

        logger.debug(f"Original Mermaid content: {mermaid_code}")
        logger.debug(f"Sanitized Mermaid content: {sanitized_code}")
        return sanitized_code
    except Exception as e:
        logger.error(f"[bold red]Error sanitizing Mermaid content:[/bold red] {str(e)}")
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
    logger.info("[bold cyan]Running Mermaid module tests...[/bold cyan]")
    for test in test_cases:
        logger.info(f"\nTesting with:\n{test}")
        process(test)
