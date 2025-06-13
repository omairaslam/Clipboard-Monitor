import subprocess
import pyperclip
from rich.console import Console
from rich.logging import RichHandler
import logging
import re
import time
import threading
import sys
import os

# Add parent directory to path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import show_notification, validate_string_input, ContentTracker

# Set up rich logging
console = Console()
logger = logging.getLogger("markdown_module")

# Global content tracker to prevent processing loops
_content_tracker = ContentTracker(max_history=5)
_processing_lock = threading.Lock()

def process(clipboard_content) -> bool:
    """Process clipboard content as markdown and convert to RTF if it appears to be markdown"""

    # Prevent concurrent processing and loops
    with _processing_lock:
        # Safety check for None or empty content
        if not validate_string_input(clipboard_content, "clipboard_content"):
            return False

        # Prevent processing the same content repeatedly
        if _content_tracker.has_processed(clipboard_content):
            logger.debug("Skipping markdown processing - content already processed recently")
            return False

        if is_markdown(clipboard_content):
            logger.info("[cyan]Markdown detected, converting to RTF...[/cyan]")
            show_notification("Markdown Detected", "Converting markdown to rich text...")

            rtf_text = convert_markdown_to_rtf(clipboard_content)
            if rtf_text:
                try:
                    # Track this content to prevent reprocessing
                    _content_tracker.add_content(clipboard_content)

                    # Copy the RTF to clipboard
                    pyperclip.copy(rtf_text)
                    logger.info("[green]Converted to RTF and copied to clipboard![/green]")
                    show_notification("Markdown Converted", "Rich text copied to clipboard!")

                    # Note: We don't restore the original markdown to avoid race conditions
                    # The user can paste the RTF where needed, and the original markdown
                    # is preserved in their clipboard history
                    return True  # Indicate that content was processed

                except pyperclip.PyperclipException as e:
                    logger.error(f"[bold red]Error copying RTF to clipboard:[/bold red] {e}")
                    return False
                except Exception as e:
                    logger.error(f"[bold red]Unexpected error during RTF copy:[/bold red] {e}")
                    return False

        return False    # Indicate that content was not processed

def is_markdown(text) -> bool:
    """Check if the text appears to be markdown with strict rules"""
    # Safety check for None or invalid content
    if not text or not isinstance(text, str):
        return False

    try:
        # Skip empty or whitespace-only text
        if not text.strip():
            return False

        # Skip if it's a mermaid diagram
        mermaid_starters = [
            "graph ", "flowchart ", "sequenceDiagram",
            "classDiagram", "stateDiagram", "erDiagram",
            "journey", "gantt", "pie", "mindmap",
            "timeline", "gitGraph", "C4Context"
        ]
        if any(text.strip().startswith(starter) for starter in mermaid_starters):
            return False

        # Strict markdown patterns
        markdown_patterns = [
            # Headers: Must start with # followed by space and text
            r'^\#{1,6}\s+[A-Za-z0-9].*$',

            # Lists: Must start with * or - followed by space and text
            r'^\s*[\*\-]\s+[A-Za-z0-9].*$',

            # Blockquotes: Must start with > followed by space and text
            r'^\s*>\s+[A-Za-z0-9].*$',

            # Code blocks: Must be properly fenced with optional language
            r'^```[a-zA-Z0-9]*\s*$',

            # Bold: Must have content between ** with word boundaries
            r'.*\*\*\b[A-Za-z0-9]+[^*]*\b\*\*.*',

            # Italic: Must have content between single * with word boundaries
            r'.*\b\*[A-Za-z0-9]+[^*]*\b\*.*',

            # Links: Must be properly formatted [text](url)
            r'.*\[[^\]]+\]\([^\)]+\).*',

            # Tables: Must have | with content between them
            r'^\|[^\|]+\|[^\|]*\|.*$'
        ]

        # Compile patterns for better performance
        patterns = [re.compile(pattern, re.MULTILINE) for pattern in markdown_patterns]

        # Check each line against patterns
        lines = text.split('\n')
        markdown_lines = 0
        total_lines = len([line for line in lines if line.strip()])

        if total_lines == 0:
            return False

        for line in lines:
            if line.strip():
                if any(pattern.match(line.strip()) for pattern in patterns):
                    markdown_lines += 1

        # Require at least 25% of non-empty lines to be markdown
        return markdown_lines > 0 and (markdown_lines / total_lines) >= 0.25

    except (AttributeError, re.error) as e:
        logger.error(f"[bold red]Error checking markdown patterns:[/bold red] {e}")
        return False
    except Exception as e:
        logger.error(f"[bold red]Unexpected error in markdown detection:[/bold red] {e}")
        return False

def convert_markdown_to_rtf(markdown_text: str) -> str:
    """Convert markdown text to RTF using pandoc with complete formatting options"""
    if not markdown_text or not isinstance(markdown_text, str):
        logger.error("[bold red]Invalid markdown text provided for conversion[/bold red]")
        return None

    try:
        process = subprocess.Popen(
            [
                'pandoc',
                '-f', 'markdown+smart+auto_identifiers',  # Enhanced markdown input
                '-t', 'rtf',                             # RTF output
                '--wrap=none',                           # Don't wrap text
                '--standalone',                          # Complete document
                '--columns=10000'                        # Prevent unwanted line breaks
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Set a timeout to prevent hanging
        try:
            rtf_text, errors = process.communicate(
                input=markdown_text.encode('utf-8'),
                timeout=30  # 30 second timeout
            )
        except subprocess.TimeoutExpired:
            process.kill()
            logger.error("[bold red]Pandoc conversion timed out[/bold red]")
            return None

        if process.returncode != 0:
            error_msg = errors.decode('utf-8') if errors else "Unknown pandoc error"
            logger.error(f"[bold red]Pandoc conversion failed:[/bold red] {error_msg}")
            return None

        if errors:
            # Log warnings but don't fail
            logger.warning(f"[bold yellow]Pandoc warnings:[/bold yellow] {errors.decode('utf-8')}")

        result = rtf_text.decode('utf-8')
        if not result.strip():
            logger.error("[bold red]Pandoc produced empty RTF output[/bold red]")
            return None

        return result

    except FileNotFoundError:
        logger.error("[bold red]Pandoc is not installed. Please install pandoc to convert markdown to RTF.[/bold red]")
        logger.info("Install using: brew install pandoc")
        return None
    except UnicodeDecodeError as e:
        logger.error(f"[bold red]Unicode error during conversion:[/bold red] {e}")
        return None
    except Exception as e:
        logger.error(f"[bold red]Unexpected error during conversion:[/bold red] {str(e)}")
        return None

# For testing
if __name__ == '__main__':
    # Set up logging for testing
    logging.basicConfig(level=logging.DEBUG)

    test_markdown = """
# Test Heading
This is a test of *italic* and **bold** text.

* List item 1
* List item 2

> This is a blockquote

```python
print("Hello World")
```
"""

    print("Testing markdown detection...")
    if is_markdown(test_markdown):
        print("✓ Markdown detected correctly")
        print("Testing conversion...")
        result = process(test_markdown)
        if result:
            print("✓ Markdown processed successfully")
        else:
            print("✗ Markdown processing failed")
    else:
        print("✗ Markdown detection failed")

    # Test edge cases
    print("\nTesting edge cases...")
    test_cases = [
        ("", "Empty string"),
        (None, "None value"),
        ("Just plain text", "Plain text"),
        ("graph TD\nA --> B", "Mermaid diagram"),
    ]

    for test_input, description in test_cases:
        result = is_markdown(test_input)
        print(f"  {description}: {'✓' if not result else '✗'} (should be False)")
