import os
import importlib
import importlib.util
from rich.console import Console
from rich.logging import RichHandler
import logging
import time
import pyperclip # Cross-platform clipboard library
import threading
from utils import show_notification

# Configuration
CONFIG = {
    'notification_title': 'Clipboard Monitor',
    'polling_interval': 1.0,
    'module_validation_timeout': 5.0
}

# Set up rich logging
console = Console()
logging.basicConfig(
    level=logging.INFO,  # Fixed: Use proper logging level constant
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console)]
) # Configure basic logging with RichHandler for pretty console output.
logger = logging.getLogger("clipboard_monitor")

# Attempt to import pyobjc for enhanced clipboard monitoring on macOS.
try:
    from AppKit import NSPasteboard, NSApplication, NSObject
    from Foundation import NSNotificationCenter, NSTimer, NSRunLoop, NSDefaultRunLoopMode
    import objc # For @objc.selector decorator
    MACOS_ENHANCED = True
    logger.debug("pyobjc loaded successfully. Enhanced monitoring enabled for macOS.")
except ImportError:
    # If pyobjc is not found, set a flag to fall back to polling.
    logger.warning("[bold yellow]pyobjc not found. Falling back to polling clipboard monitoring.[/bold yellow]")
    logger.warning("[bold yellow]For enhanced monitoring on macOS, install it: pip install pyobjc-framework-Cocoa[/bold yellow]")
    MACOS_ENHANCED = False



class ClipboardMonitor:
    """
    Manages the loading of processing modules and orchestrates clipboard content processing.
    """
    def __init__(self):
        """Initializes the ClipboardMonitor with an empty list of modules."""
        self.modules = []
        self.processing_lock = threading.Lock()  # Prevent concurrent processing
        self.last_processed_hash = None  # Track processed content to prevent loops

    def _validate_module(self, module) -> bool:
        """Validate that a module has the required interface."""
        if not hasattr(module, 'process'):
            logger.error(f"[bold red]Module {getattr(module, '__name__', 'unknown')} missing 'process' function[/bold red]")
            return False

        if not callable(getattr(module, 'process')):
            logger.error(f"[bold red]Module {getattr(module, '__name__', 'unknown')} 'process' is not callable[/bold red]")
            return False

        return True

    def load_modules(self, module_dir: str) -> None:
        """
        Dynamically loads Python modules from the specified directory.
        Each module is expected to have a 'process(clipboard_content)' function.
        """
        if not os.path.exists(module_dir):
            logger.error(f"[bold red]Module directory does not exist:[/bold red] {module_dir}")
            return

        if not os.path.isdir(module_dir):
            logger.error(f"[bold red]Module path is not a directory:[/bold red] {module_dir}")
            return

        try:
            module_files = [f for f in os.listdir(module_dir) if f.endswith('.py') and not f.startswith('__')]
        except OSError as e:
            logger.error(f"[bold red]Error reading module directory:[/bold red] {e}")
            return

        for module_file in module_files:
            module_name = module_file[:-3]
            module_path = os.path.join(module_dir, module_file)

            try:
                # Create a module spec from the file location.
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if spec is None or spec.loader is None:
                    logger.error(f"[bold red]Could not create module spec for:[/bold red] {module_name}")
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module) # Execute the module to make its content available.

                # Validate module interface
                if not self._validate_module(module):
                    continue

                self.modules.append(module) # Add the loaded module to the list.
                logger.info(f"[bold green]Loaded module:[/bold green] {module_name}")

            except Exception as e:
                logger.error(f"[bold red]Error loading module {module_name}:[/bold red] {e}")

    def _get_content_hash(self, content) -> str:
        """Generate a hash of the content to detect processing loops."""
        import hashlib
        if content is None:
            return "none"
        return hashlib.md5(str(content).encode()).hexdigest()

    def process_clipboard(self, clipboard_content) -> bool:
        """Process clipboard content with all modules. Returns True if any module processed it."""
        # Prevent concurrent processing and infinite loops
        with self.processing_lock:
            content_hash = self._get_content_hash(clipboard_content)
            if content_hash == self.last_processed_hash:
                logger.debug("Skipping processing - content hash matches last processed")
                return False

            self.last_processed_hash = content_hash
            processed = False

            for module in self.modules:
                try:
                    # Call the 'process' function of each loaded module.
                    if module.process(clipboard_content):
                        processed = True
                        logger.info(f"[cyan]Processed clipboard content with module:[/cyan] {getattr(module, '__name__', 'unknown')}")
                except Exception as e:
                    logger.error(f"[bold red]Error processing with module {getattr(module, '__name__', 'unknown')}:[/bold red] {e}")

            # If no module processed the content, and the original content was not None
            # (i.e., it was actual text), ensure it's still in the clipboard.
            # This avoids issues like trying to pyperclip.copy(None) if paste() returned None
            # for non-text content like an image.
            if not processed and clipboard_content is not None:
                try:
                    pyperclip.copy(clipboard_content)
                except pyperclip.PyperclipException as e:
                    logger.error(f"[bold red]Error restoring clipboard content:[/bold red] {e}")
            elif not processed and clipboard_content is None:
                # If content was None (e.g., an image was copied) and no module processed it,
                # log this but don't try to copy 'None' back to the clipboard.
                logger.debug("Non-text or empty content from clipboard was not processed; clipboard unchanged by script.")

            return processed

# Check if enhanced monitoring is enabled (pyobjc was successfully imported).
if MACOS_ENHANCED:
    class ClipboardMonitorHandler(NSObject):
        """
        An Objective-C compatible class that uses NSTimer to efficiently monitor clipboard changes.
        This class is instantiated and used only if MACOS_ENHANCED is True.
        """

        def initWithMonitor_andInitialContent_(self, monitor_instance, initial_clipboard_content):
            """
            Custom initializer for the Objective-C object.
            Stores the ClipboardMonitor instance and tracks clipboard changes.
            """
            self = objc.super(ClipboardMonitorHandler, self).init()
            if self is None:
                return None

            self.monitor_instance = monitor_instance
            self.pasteboard = NSPasteboard.generalPasteboard()
            self.last_change_count = self.pasteboard.changeCount()
            self.last_processed_clipboard_content = initial_clipboard_content
            self.processing_in_progress = False  # Flag to prevent recursive processing
            self.timer = None
            logger.debug(f"ClipboardMonitorHandler initialized. Initial changeCount: {self.last_change_count}")
            return self

        @objc.selector
        def checkClipboardChange_(self, timer):
            """
            Timer callback method that checks for clipboard changes using changeCount.
            This is more efficient than polling the actual clipboard content.
            """
            # Prevent recursive processing if a module modifies the clipboard
            if self.processing_in_progress:
                return

            current_change_count = self.pasteboard.changeCount()
            if current_change_count != self.last_change_count:
                self.last_change_count = current_change_count

                try:
                    current_clipboard_content = pyperclip.paste()
                except pyperclip.PyperclipException as e:
                    logger.error(f"[bold red]Error reading clipboard via pyperclip in timer handler:[/bold red] {e}")
                    return
                except Exception as e:
                    logger.error(f"[bold red]Unexpected error reading clipboard in timer handler:[/bold red] {e}")
                    return

                # Avoid processing if content hasn't actually changed
                if current_clipboard_content == self.last_processed_clipboard_content:
                    logger.debug("Clipboard content identical to last processed content. Skipping.")
                    return

                # Set processing flag to prevent recursion
                self.processing_in_progress = True

                try:
                    # Update the last processed content to the current content.
                    self.last_processed_clipboard_content = current_clipboard_content

                    logger.info("[bold blue]Clipboard changed (enhanced monitoring)![/bold blue]")
                    show_notification(CONFIG['notification_title'], "Clipboard changed (enhanced)!")

                    # If the monitor instance is available, process the new clipboard content.
                    if self.monitor_instance:
                        try:
                            self.monitor_instance.process_clipboard(current_clipboard_content)
                        except Exception as e:
                            # Log any errors during the processing by the modules.
                            logger.error(f"[bold red]Error during monitor.process_clipboard from timer handler:[/bold red] {e}")
                    else:
                        logger.error("[bold red]Monitor instance not available in ClipboardMonitorHandler[/bold red]")
                finally:
                    # Always reset the processing flag
                    self.processing_in_progress = False

        def startMonitoring(self):
            """Start the timer-based monitoring."""
            if self.timer is None:
                # Create a timer that fires every 0.1 seconds (much more responsive than 1 second polling)
                self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                    0.1, self, objc.selector(self.checkClipboardChange_, signature=b'v@:@'), None, True
                )
                logger.debug("Enhanced clipboard monitoring timer started")

        def stopMonitoring(self):
            """Stop the timer-based monitoring."""
            if self.timer:
                self.timer.invalidate()
                self.timer = None
                logger.debug("Enhanced clipboard monitoring timer stopped")

        def cleanup(self):
            """Clean up resources when shutting down."""
            self.stopMonitoring()
            self.monitor_instance = None
            self.last_processed_clipboard_content = None
            self.pasteboard = None

def main():
    monitor = ClipboardMonitor()
    modules_dir = os.path.join(os.path.dirname(__file__), 'modules')
    monitor.load_modules(modules_dir)

    if not monitor.modules:
        logger.warning("[bold yellow]No modules loaded. Monitor will run but won't process clipboard content.[/bold yellow]")

    # --- Enhanced Monitoring Path (macOS with pyobjc) ---
    if MACOS_ENHANCED:
        logger.info("[bold green]Using enhanced clipboard monitoring (macOS).[/bold green]")

        initial_clipboard_content = None
        try:
            # Get the initial clipboard content when the script starts.
            initial_clipboard_content = pyperclip.paste()
            if initial_clipboard_content: # Only process if there's something initially
                logger.info("Processing initial clipboard content (enhanced mode)...")
                # Process this initial content once.
                monitor.process_clipboard(initial_clipboard_content)
        except pyperclip.PyperclipException as e:
            logger.error(f"[bold red]Error reading initial clipboard content (enhanced):[/bold red] {e}")
        except Exception as e:
            logger.error(f"[bold red]Error processing initial clipboard content (enhanced):[/bold red] {e}")

        try:
            app = NSApplication.sharedApplication() # Get a shared NSApplication instance
            # Create an instance of our monitor handler, passing the monitor and initial content.
            handler_instance = ClipboardMonitorHandler.alloc().initWithMonitor_andInitialContent_(monitor, initial_clipboard_content)

            # Start the timer-based monitoring
            handler_instance.startMonitoring()

            logger.info("[bold yellow]Enhanced clipboard monitor started. Press Ctrl+C to exit.[/bold yellow]")

            try:
                app.run() # Start the Cocoa event loop. This call will block and keep the script running,
                          # with the timer checking for clipboard changes.
            except KeyboardInterrupt:
                logger.info("[bold yellow]Keyboard interrupt received in enhanced mode.[/bold yellow]")
            finally:
                # Clean up the handler
                if handler_instance:
                    handler_instance.cleanup()

        except Exception as e:
            logger.error(f"[bold red]Error setting up enhanced monitoring:[/bold red] {e}")
            logger.info("[bold yellow]Falling back to polling mode...[/bold yellow]")
            # Fall through to polling mode
        else:
            # This line is unlikely to be reached if Ctrl+C terminates the app directly.
            logger.info("[bold yellow]Enhanced clipboard monitor shut down.[/bold yellow]")
            return

    # --- Polling Monitoring Path (Fallback if pyobjc is not available or not on macOS) ---
    # This will also be reached if event-driven setup fails
    logger.info("[bold yellow]Clipboard monitor started (polling).[/bold yellow]")
    last_clipboard = None
    consecutive_errors = 0
    max_consecutive_errors = 10

    try:
        # Process initial clipboard content for polling mode too
        initial_clipboard_content = pyperclip.paste()
        if initial_clipboard_content:
            # Process the initial content once.
            logger.info("Processing initial clipboard content (polling)...")
            last_clipboard = initial_clipboard_content # Set for the first comparison
            monitor.process_clipboard(initial_clipboard_content)
    except pyperclip.PyperclipException as e:
        logger.error(f"[bold red]Error reading initial clipboard content (polling):[/bold red] {e}")
    except Exception as e:
        logger.error(f"[bold red]Error processing initial clipboard content (polling):[/bold red] {e}")

    # Main polling loop.
    try:
        while True:
            try:
                clipboard_content = pyperclip.paste()
                # If the current clipboard content is different from the last known content.
                if clipboard_content != last_clipboard:
                    last_clipboard = clipboard_content
                    show_notification(CONFIG['notification_title'], "Clipboard changed (polling)!")
                    monitor.process_clipboard(clipboard_content)

                # Reset error counter on successful iteration
                consecutive_errors = 0
                time.sleep(CONFIG['polling_interval'])  # Configurable polling interval

            except pyperclip.PyperclipException as e:
                consecutive_errors += 1
                logger.error(f"[bold red]pyperclip error in polling loop (#{consecutive_errors}):[/bold red] {e}")

                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"[bold red]Too many consecutive pyperclip errors ({consecutive_errors}). Exiting.[/bold red]")
                    break

                time.sleep(5) # Wait longer if there's a persistent pyperclip issue to avoid spamming errors.

            except Exception as e:
                consecutive_errors += 1
                logger.error(f"[bold red]Unexpected error in polling loop (#{consecutive_errors}):[/bold red] {e}")

                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"[bold red]Too many consecutive errors ({consecutive_errors}). Exiting.[/bold red]")
                    break

                time.sleep(1) # Brief pause before retrying

    except KeyboardInterrupt: # Handle Ctrl+C to gracefully stop the monitor.
        logger.info("[bold yellow]\nClipboard monitor stopped by user (polling).[/bold yellow]")
    except Exception as e:
        logger.error(f"[bold red]Fatal error in polling loop:[/bold red] {e}")
    finally:
        logger.info("[bold yellow]Clipboard monitor shutdown complete.[/bold yellow]")

# Standard Python entry point.
if __name__ == "__main__":
    main()
