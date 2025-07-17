#!/usr/bin/env python3
"""
Command-line clipboard history viewer and manager
"""

import os
import json
import datetime
import pyperclip
import sys
from utils import load_clipboard_history

from modules.history_module import load_history as _load_history

# Exported for test compatibility
def load_history():
    """Load clipboard history using the main history module (for tests)."""
    return _load_history()

# ANSI color codes for terminal formatting
class Colors:
    # Basic colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'

    # Reset
    RESET = '\033[0m'

    # Background colors
    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'
    BG_RED = '\033[41m'

    @staticmethod
    def colorize(text, color):
        """Add color to text"""
        return f"{color}{text}{Colors.RESET}"

def display_history(history):
    """Display clipboard history in terminal with colors and formatting"""
    if not history:
        print(Colors.colorize("📭 No clipboard history found.", Colors.YELLOW))
        print(Colors.colorize("💡 Copy something to start tracking your clipboard history!", Colors.CYAN))
        return

    # Header with colors
    header = f"📋 Clipboard History ({len(history)} items)"
    print(Colors.colorize(header, Colors.BOLD + Colors.BLUE))
    print(Colors.colorize("═" * 80, Colors.BLUE))

    for i, item in enumerate(history):
        try:
            timestamp = datetime.datetime.fromtimestamp(item.get('timestamp', 0))
            content = item.get('content', '').strip()

            # Format timestamp with color
            time_str = timestamp.strftime('%m/%d %H:%M')
            colored_time = Colors.colorize(time_str, Colors.CYAN)

            # Truncate content for list view with special handling for RTF
            if content.startswith('{\\rtf') or (content.startswith('{') and 'deff0' in content and 'ttbl' in content):
                # For RTF content, show a more user-friendly preview
                display_content = "🎨 RTF Content (converted from Markdown)"
            else:
                display_content = content[:70].replace('\n', ' ').replace('\r', ' ')
                if len(content) > 70:
                    display_content += '...'

            # Color coding based on item age and type
            if i == 0:
                # Most recent item - bright green
                item_num = Colors.colorize(f"[{i+1:2d}]", Colors.BOLD + Colors.GREEN)
                content_color = Colors.GREEN
            elif i < 5:
                # Recent items - yellow
                item_num = Colors.colorize(f"[{i+1:2d}]", Colors.YELLOW)
                content_color = Colors.WHITE
            else:
                # Older items - dim
                item_num = Colors.colorize(f"[{i+1:2d}]", Colors.DIM)
                content_color = Colors.DIM

            # Format content with appropriate color
            colored_content = Colors.colorize(display_content, content_color)

            # Print formatted line
            separator = Colors.colorize("│", Colors.BLUE)
            print(f"{item_num} {colored_time} {separator} {colored_content}")

        except Exception as e:
            error_msg = f"[{i+1:2d}] Error displaying item: {e}"
            print(Colors.colorize(error_msg, Colors.RED))

    print(Colors.colorize("═" * 80, Colors.BLUE))

def show_item_detail(history, item_num):
    """Show detailed view of a specific item with colors"""
    if item_num < 1 or item_num > len(history):
        error_msg = f"❌ Invalid item number. Please choose 1-{len(history)}"
        print(Colors.colorize(error_msg, Colors.RED))
        return

    item = history[item_num - 1]
    timestamp = datetime.datetime.fromtimestamp(item.get('timestamp', 0))
    content = item.get('content', '')

    # Header with colors
    header = f"📄 Item #{item_num} Details"
    print(Colors.colorize(f"\n{header}", Colors.BOLD + Colors.BLUE))
    print(Colors.colorize("═" * 80, Colors.BLUE))

    # Metadata with colors
    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    print(f"{Colors.colorize('📅 Timestamp:', Colors.CYAN)} {Colors.colorize(timestamp_str, Colors.WHITE)}")
    print(f"{Colors.colorize('📏 Length:', Colors.CYAN)} {Colors.colorize(f'{len(content)} characters', Colors.WHITE)}")

    # Content type detection
    content_type = "Text"
    if content.startswith(('http://', 'https://')):
        content_type = "🔗 URL"
    elif content.startswith('file://'):
        content_type = "📁 File Path"
    elif content.startswith('{\\rtf') or (content.startswith('{') and 'deff0' in content and 'ttbl' in content):
        content_type = "🎨 RTF (Rich Text Format)"
    elif '\n' in content and len(content.split('\n')) > 3:
        content_type = "📝 Multi-line Text"
    elif any(keyword in content.lower() for keyword in ['password', 'token', 'key', 'secret']):
        content_type = "🔐 Sensitive Data"

    print(f"{Colors.colorize('📋 Type:', Colors.CYAN)} {Colors.colorize(content_type, Colors.YELLOW)}")

    print(Colors.colorize("─" * 80, Colors.DIM))

    # Content with syntax highlighting for certain types
    if content.startswith(('http://', 'https://')):
        print(Colors.colorize(content, Colors.BLUE + Colors.UNDERLINE))
    elif content.startswith('file://'):
        print(Colors.colorize(content, Colors.MAGENTA))
    elif content.startswith('{\\rtf') or (content.startswith('{') and 'deff0' in content and 'ttbl' in content):
        # RTF content - show both raw and a note about conversion
        print(Colors.colorize("Raw RTF Content:", Colors.YELLOW))
        print(Colors.colorize(content, Colors.DIM))
        print(Colors.colorize("\n💡 This is RTF (Rich Text Format) content, likely converted from Markdown.", Colors.CYAN))
        print(Colors.colorize("   When pasted into applications that support RTF, it will appear formatted.", Colors.CYAN))
    else:
        print(Colors.colorize(content, Colors.WHITE))

    print(Colors.colorize("─" * 80, Colors.DIM))

def copy_item(history, item_num):
    """Copy specific item to clipboard with colored feedback"""
    if item_num < 1 or item_num > len(history):
        error_msg = f"❌ Invalid item number. Please choose 1-{len(history)}"
        print(Colors.colorize(error_msg, Colors.RED))
        return False

    try:
        item = history[item_num - 1]
        content = item.get('content', '')
        pyperclip.copy(content)

        # Success message with colors
        success_msg = f"✅ Item #{item_num} copied to clipboard!"
        print(Colors.colorize(success_msg, Colors.GREEN))

        # Show preview of what was copied
        preview = content[:50].replace('\n', ' ').replace('\r', ' ')
        if len(content) > 50:
            preview += '...'
        preview_msg = f"📋 Copied: {preview}"
        print(Colors.colorize(preview_msg, Colors.CYAN))

        # Indicate that the list will refresh
        refresh_msg = "🔄 List will refresh to show this item at the top..."
        print(Colors.colorize(refresh_msg, Colors.YELLOW))

        # Note about clipboard monitor delay
        note_msg = "💡 Note: It may take a few seconds for the clipboard monitor to detect the change"
        print(Colors.colorize(note_msg, Colors.DIM))

        # Add a visual separator for the refresh
        print(Colors.colorize("⬇️  ⬇️  ⬇️", Colors.GREEN))

        return True
    except Exception as e:
        error_msg = f"❌ Failed to copy item: {e}"
        print(Colors.colorize(error_msg, Colors.RED))
        return False

def clear_history():
    """Clear all clipboard history with confirmation"""
    try:
        # Load current history to show count        
        history = load_clipboard_history()
        if not history:
            print(Colors.colorize("📭 No history to clear.", Colors.YELLOW))
            return

        # Show confirmation with colors
        print(Colors.colorize(f"\n🗑️  CLEAR CLIPBOARD HISTORY", Colors.BOLD + Colors.RED))
        print(Colors.colorize("═" * 50, Colors.RED))
        print(Colors.colorize(f"📊 Current history: {len(history)} items", Colors.WHITE))
        print(Colors.colorize("⚠️  This action cannot be undone!", Colors.YELLOW))

        # Get confirmation
        prompt = Colors.colorize("\n❓ Are you sure you want to clear all history? (y/N): ", Colors.CYAN)
        response = input(prompt).strip().lower()


        if response in ['y', 'yes']:
            # Use the robust clear_history from the main history module
            try:
                from modules.history_module import clear_history as module_clear_history
                result = module_clear_history()
                if result:
                    print(Colors.colorize("\n✅ History cleared successfully!", Colors.GREEN))
                    print(Colors.colorize("📭 All clipboard history has been removed.", Colors.GREEN))
                    print(Colors.colorize("💡 Copy something to start tracking again.", Colors.CYAN))
                else:
                    print(Colors.colorize("❌ Failed to clear history file.", Colors.RED))
            except Exception as file_error:
                error_msg = f"❌ Failed to clear history file: {file_error}"
                print(Colors.colorize(error_msg, Colors.RED))
        else:
            print(Colors.colorize("\n🚫 Clear operation cancelled.", Colors.YELLOW))

    except Exception as e:
        error_msg = f"❌ Error during clear operation: {e}"
        print(Colors.colorize(error_msg, Colors.RED))

def interactive_mode():
    """Run interactive clipboard history manager with enhanced UI"""
    # Clear screen for better presentation
    os.system('clear' if os.name == 'posix' else 'cls')

    while True:
        # Header with gradient-like effect
        print("\n" + Colors.colorize("═" * 80, Colors.BLUE))
        title = "📋 CLIPBOARD HISTORY MANAGER"
        print(Colors.colorize(title.center(80), Colors.BOLD + Colors.WHITE + Colors.BG_BLUE))
        print(Colors.colorize("═" * 80, Colors.BLUE))

        history = load_clipboard_history()
        display_history(history)

        if not history:
            print(Colors.colorize("\n💡 Press Enter to refresh or 'q' to quit...", Colors.YELLOW))
            choice = input(Colors.colorize("➤ ", Colors.GREEN)).strip().lower()
            if choice == 'q':
                break
            continue

        # Commands section with colors
        print(Colors.colorize("\n🎯 COMMANDS:", Colors.BOLD + Colors.YELLOW))
        commands = [
            ("  [number]", "Copy item to clipboard", "(e.g., '1', '2', '3') - auto-refreshes"),
            ("  d [number]", "Show detailed view", "(e.g., 'd 1')"),
            ("  r", "Refresh history manually", ""),
            ("  w", "Open web viewer", ""),
            ("  clear", "Clear all history", ""),
            ("  c", "Clear screen", ""),
            ("  q", "Quit", "")
        ]

        for cmd, desc, example in commands:
            cmd_colored = Colors.colorize(cmd, Colors.CYAN)
            desc_colored = Colors.colorize(desc, Colors.WHITE)
            example_colored = Colors.colorize(example, Colors.DIM)
            print(f"{cmd_colored} - {desc_colored} {example_colored}")

        # Input prompt with color
        prompt = Colors.colorize("\n➤ Enter command: ", Colors.GREEN + Colors.BOLD)
        choice = input(prompt).strip().lower()
        
        if choice == 'q':
            print(Colors.colorize("\n👋 Goodbye! Thanks for using Clipboard History Manager!", Colors.GREEN))
            break
        elif choice == 'r':
            print(Colors.colorize("🔄 Refreshing history...", Colors.YELLOW))
            continue
        elif choice == 'clear':
            clear_history()
            input(Colors.colorize("\nPress Enter to continue...", Colors.DIM))
            continue
        elif choice == 'c':
            os.system('clear' if os.name == 'posix' else 'cls')
            continue
        elif choice == 'w':
            try:
                import subprocess
                web_viewer = os.path.join(os.path.dirname(__file__), 'web_history_viewer.py')
                subprocess.Popen([sys.executable, web_viewer])
                success_msg = "🌐 Web viewer opened in browser"
                print(Colors.colorize(success_msg, Colors.GREEN))
            except Exception as e:
                error_msg = f"❌ Failed to open web viewer: {e}"
                print(Colors.colorize(error_msg, Colors.RED))
        elif choice.startswith('d '):
            try:
                item_num = int(choice.split()[1])
                show_item_detail(history, item_num)
                input(Colors.colorize("\nPress Enter to continue...", Colors.DIM))
            except (ValueError, IndexError):
                error_msg = "❌ Invalid command. Use 'd [number]' (e.g., 'd 1')"
                print(Colors.colorize(error_msg, Colors.RED))
        elif choice.isdigit():
            item_num = int(choice)
            if copy_item(history, item_num):
                # Ask user if they want to wait for refresh
                refresh_prompt = Colors.colorize("\n🔄 Wait for auto-refresh? (y/n, default=y): ", Colors.CYAN)
                refresh_choice = input(refresh_prompt).strip().lower()

                if refresh_choice != 'n':
                    print(Colors.colorize("⏳ Waiting for clipboard monitor to update...", Colors.YELLOW))
                    # Longer delay to allow the clipboard monitor to update the history file
                    import time
                    time.sleep(1.5)
                    # Clear screen for clean refresh
                    os.system('clear' if os.name == 'posix' else 'cls')
                    # Continue to next iteration to refresh the display
                    continue
                else:
                    print(Colors.colorize("✅ Copy completed. Use 'r' to manually refresh later.", Colors.GREEN))
        else:
            error_msg = "❌ Invalid command. Try again."
            print(Colors.colorize(error_msg, Colors.RED))

def main():
    """Main function with enhanced command-line interface"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()        
        history = load_clipboard_history()

        if command == 'list' or command == 'ls':
            display_history(history)
        elif command == 'copy' and len(sys.argv) > 2:
            try:
                item_num = int(sys.argv[2])
                if copy_item(history, item_num):
                    # Show updated list after copy
                    print(Colors.colorize("\n🔄 Waiting for clipboard monitor to update...", Colors.YELLOW))
                    import time
                    time.sleep(1.5)  # Allow clipboard monitor to update
                    updated_history = load_clipboard_history()

                    # Check if the history was actually updated
                    if len(updated_history) > len(history) or (updated_history and updated_history[0] != history[0]):
                        print(Colors.colorize("✅ History updated! Showing refreshed list:", Colors.GREEN))
                    else:
                        print(Colors.colorize("⏳ History may still be updating. Showing current list:", Colors.YELLOW))

                    display_history(updated_history)
            except ValueError:
                error_msg = "❌ Invalid item number"
                print(Colors.colorize(error_msg, Colors.RED))
        elif command == 'show' and len(sys.argv) > 2:
            try:
                item_num = int(sys.argv[2])
                show_item_detail(history, item_num)
            except ValueError:
                error_msg = "❌ Invalid item number"
                print(Colors.colorize(error_msg, Colors.RED))
        elif command == 'web':
            try:
                import subprocess
                web_viewer = os.path.join(os.path.dirname(__file__), 'web_history_viewer.py')
                subprocess.Popen([sys.executable, web_viewer])
                success_msg = "🌐 Web viewer opened in browser"
                print(Colors.colorize(success_msg, Colors.GREEN))
            except Exception as e:
                error_msg = f"❌ Failed to open web viewer: {e}"
                print(Colors.colorize(error_msg, Colors.RED))
        elif command == 'clear':
            clear_history()
        else:
            # Enhanced usage display with colors
            print(Colors.colorize("📋 Clipboard History Viewer - Usage:", Colors.BOLD + Colors.BLUE))
            print(Colors.colorize("═" * 50, Colors.BLUE))

            usage_items = [
                ("python3 cli_history_viewer.py", "Interactive mode", "🎯"),
                ("python3 cli_history_viewer.py list", "List all items", "📋"),
                ("python3 cli_history_viewer.py copy [num]", "Copy item to clipboard", "📄"),
                ("python3 cli_history_viewer.py show [num]", "Show item details", "🔍"),
                ("python3 cli_history_viewer.py web", "Open web viewer", "🌐"),
                ("python3 cli_history_viewer.py clear", "Clear all history", "🗑️")
            ]

            for cmd, desc, icon in usage_items:
                cmd_colored = Colors.colorize(cmd, Colors.CYAN)
                desc_colored = Colors.colorize(f"{icon} {desc}", Colors.WHITE)
                print(f"  {cmd_colored}")
                print(f"    {desc_colored}\n")
    else:
        interactive_mode()

if __name__ == "__main__":
    main()

import datetime
import os

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

# Replace all logger.info, logger.warning, logger.error, logger.debug calls with log_event or log_error as appropriate
