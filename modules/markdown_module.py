import subprocess
import pyperclip
import logging
import re
import time
import threading
import sys
import os
import json
import datetime

try:
    # Try relative import first (when run as module)
    from ..utils import show_notification, validate_string_input, ContentTracker, get_config, log_event, log_error
except ImportError:
    # Fallback to adding parent directory to path (for standalone testing)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils import show_notification, validate_string_input, ContentTracker, get_config, log_event, log_error

logger = logging.getLogger("markdown_module")

# Global content tracker to prevent processing loops
_content_tracker = ContentTracker(max_history=5)
_processing_lock = threading.Lock()

def process(clipboard_content, config=None) -> bool:
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
            logger.info("Markdown detected!")

            # Check if clipboard modification is enabled for markdown
            # Use module_config passed from main, or load if not provided (for standalone testing)
            modify_clipboard = (config or get_config('modules')).get('markdown_modify_clipboard', True)

            if modify_clipboard:
                logger.info("[cyan]Converting markdown to RTF...[/cyan]")
                show_notification("Markdown Detected", "Converting markdown to rich text...", "")

                rtf_text = convert_markdown_to_rtf(clipboard_content)
                if rtf_text:
                    try:
                        # Track this content to prevent reprocessing
                        _content_tracker.add_content(clipboard_content)

                        # Use pbcopy to set RTF content directly (macOS specific)
                        # pbcopy automatically detects RTF if content starts with RTF header
                        logger.info("[bold blue]ATTEMPTING TO USE PBCOPY METHOD FOR RTF CLIPBOARD HANDLING[/bold blue]")
                        try:
                            subprocess.run(
                                ['pbcopy'],
                                input=rtf_text.encode('utf-8'),
                                check=True,
                                timeout=5
                            )
                            logger.info("[green]SUCCESS: Used pbcopy for RTF clipboard handling[/green]")
                            logger.info("[green]Converted to RTF and copied to clipboard![/green]")
                            show_notification("Markdown Converted", "Rich text copied to clipboard!", "")
                            
                            # Indicate that clipboard was modified. Main app will handle history.
                            return True 

                        except subprocess.SubprocessError as e:
                            logger.error(f"[bold red]Error using pbcopy for RTF:[/bold red] {e}")
                            # Fall back to pyperclip if pbcopy fails
                            logger.info("[yellow]FALLING BACK TO PYPERCLIP METHOD FOR RTF CLIPBOARD HANDLING[/yellow]")
                            pyperclip.copy(rtf_text)
                            logger.info("[yellow]Used pyperclip fallback for RTF copy[/yellow]")

                            # Indicate that clipboard was modified. Main app will handle history.
                            return True

                            return True

                    except pyperclip.PyperclipException as e:
                        logger.error(f"[bold red]Error copying RTF to clipboard:[/bold red] {e}")
                        return False
                    except Exception as e:
                        logger.error(f"[bold red]Unexpected error during RTF copy:[/bold red] {e}")
                        return False
            else:
                # Read-only mode: just notify about markdown detection
                show_notification("Markdown Detected", "Markdown detected (read-only mode)", "")
                logger.info("[blue]Markdown detected but clipboard modification disabled[/blue]")
                return False  # Don't modify clipboard

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
        # First convert markdown to HTML as an intermediate format
        html_process = subprocess.Popen(
            [
                'pandoc',
                '-f', 'markdown+smart+auto_identifiers',
                '-t', 'html',
                '--wrap=none',
                '--standalone'
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Set a timeout to prevent hanging
        try:
            html_output, errors = html_process.communicate(
                input=markdown_text.encode('utf-8'),
                timeout=15  # 15 second timeout
            )
        except subprocess.TimeoutExpired:
            html_process.kill()
            logger.error("[bold red]HTML conversion timed out[/bold red]")
            return None

        if html_process.returncode != 0:
            error_msg = errors.decode('utf-8') if errors else "Unknown pandoc error"
            logger.error(f"[bold red]HTML conversion failed:[/bold red] {error_msg}")
            return None

        # Then convert HTML to RTF using textutil (macOS only)
        rtf_process = subprocess.Popen(
            [
                'textutil',
                '-stdin',
                '-stdout',
                '-format', 'html',
                '-convert', 'rtf'
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        try:
            rtf_output, rtf_errors = rtf_process.communicate(
                input=html_output,
                timeout=15  # 15 second timeout
            )
        except subprocess.TimeoutExpired:
            rtf_process.kill()
            logger.error("[bold red]RTF conversion timed out[/bold red]")
            return None

        if rtf_process.returncode != 0:
            error_msg = rtf_errors.decode('utf-8') if rtf_errors else "Unknown textutil error"
            logger.error(f"[bold red]RTF conversion failed:[/bold red] {error_msg}")
            return None

        result = rtf_output.decode('utf-8')
        if not result.strip():
            logger.error("[bold red]Conversion produced empty RTF output[/bold red]")
            return None

        return result

    except FileNotFoundError as e:
        if "textutil" in str(e):
            logger.error("[bold red]textutil not found. This tool is only available on macOS.[/bold red]")
        else:
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
