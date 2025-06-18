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
import json
import subprocess
import re

def load_config():
    """Load configuration from config.json if available"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    
    # Default configuration
    config = {
        'notification_title': 'Clipboard Monitor',
        'polling_interval': 1.0,
        'module_validation_timeout': 5.0,
        'enhanced_check_interval': 0.1,
        'max_clipboard_size': 10 * 1024 * 1024,
        'debug_mode': False
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                
            # Update general settings
            if 'general' in user_config:
                for key, value in user_config['general'].items():
                    if key in config:
                        config[key] = value

            # Add support for performance, history, and security sections
            for section in ['performance', 'history', 'security']:
                if section in user_config:
                    config[section] = user_config[section]
                        
            # Note: Debug mode will be applied after logger is set up
            
            print(f"Loaded configuration from {config_path}")
        else:
            print("No config.json found, using defaults")
    except Exception as e:
        print(f"Error loading config: {e}")
        print("Using default configuration")
    
    return config

# Load configuration
CONFIG = load_config()

# Set up rich logging
console = Console()
logging.basicConfig(
    level=logging.INFO,  # Fixed: Use proper logging level constant
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console)]
) # Configure basic logging with RichHandler for pretty console output.
logger = logging.getLogger("clipboard_monitor")

# Apply debug mode if enabled in config
if CONFIG.get('debug_mode', False):
    logging.getLogger().setLevel(logging.DEBUG)
    logger.info("[bold yellow]Debug mode enabled[/bold yellow]")

# Attempt to import pyobjc for enhanced clipboard monitoring on macOS.
try:
    from AppKit import NSPasteboard, NSApplication, NSObject, NSThread
    from Foundation import NSTimer, NSDate
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

    def load_modules(self, modules_dir):
        """Load all modules from the specified directory with lazy initialization."""
        self.modules = []
        self.module_specs = []  # Store module specs for lazy loading
        
        # Load module configuration
        module_config = self._load_module_config()
        
        if not os.path.exists(modules_dir) or not os.path.isdir(modules_dir):
            logger.error(f"[bold red]Module directory issue:[/bold red] {modules_dir}")
            return

        # First pass: just collect module specs without importing
        for filename in os.listdir(modules_dir):
            if filename.endswith('_module.py'):
                module_path = os.path.join(modules_dir, filename)
                module_name = filename[:-3]  # Remove .py
                
                # Check if module is enabled
                if module_config.get(module_name, {}).get('enabled', True):
                    # Store module spec for lazy loading
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    self.module_specs.append((module_name, spec))
                    logger.info(f"[bold green]Found module:[/bold green] {module_name}")
                else:
                    logger.info(f"[bold yellow]Module disabled in config:[/bold yellow] {module_name}")

    def _load_module_config(self):
        """Load module configuration from a file."""
        config_path = os.path.expanduser('~/Library/Application Support/ClipboardMonitor/modules_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}

    def _load_module_if_needed(self, module_name, spec):
        """Lazy load a module only when needed."""
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Validate module has process function
        if not hasattr(module, 'process') or not callable(module.process):
            raise AttributeError(f"Module {module_name} missing required 'process' function")
            
        return module

    def _get_content_hash(self, content) -> str:
        """Generate a hash of the content to detect processing loops."""
        import hashlib
        if content is None:
            return "none"
        return hashlib.md5(str(content).encode()).hexdigest()

    def process_clipboard(self, clipboard_content) -> bool:
        """Process clipboard content with memory optimization."""
        # Prevent processing extremely large content
        if clipboard_content and len(clipboard_content) > CONFIG.get('security', {}).get('max_clipboard_size', 10485760):
            logger.warning(f"[bold yellow]Skipping oversized clipboard content ({len(clipboard_content)} bytes)[/bold yellow]")
            return False
        
        # Process with memory optimization (avoid duplicate copies)
        
        # Process with memory optimization
        with self.processing_lock:
            content_hash = self._get_content_hash(clipboard_content)
            if content_hash == self.last_processed_hash:
                logger.debug("Skipping processing - content hash matches last processed")
                return False

            self.last_processed_hash = content_hash
            processed = False
            
            # Lazy load modules if not already loaded
            if not self.modules and self.module_specs:
                for module_name, spec in self.module_specs:
                    try:
                        module = self._load_module_if_needed(module_name, spec)
                        self.modules.append(module)
                    except Exception as e:
                        logger.error(f"[bold red]Error loading module {module_name}:[/bold red] {e}")
            
            # Process with loaded modules
            for module in self.modules:
                try:
                    if module.process(clipboard_content):
                        processed = True
                        logger.info(f"[cyan]Processed with module:[/cyan] {getattr(module, '__name__', 'unknown')}")
                except Exception as e:
                    logger.error(f"[bold red]Error processing with module:[/bold red] {e}")
                    
            # Processing complete
        
        # Suggest garbage collection for very large content
        if clipboard_content and len(clipboard_content) > 1000000:
            import gc
            gc.collect()
        
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
        def checkClipboardChange_(self, _):
            """
            Timer callback method that checks for clipboard changes using changeCount.
            This is more efficient than polling the actual clipboard content.
            """
            # Skip checks when system is idle
            if self.processing_in_progress:
                return
            
            # Adaptive checking interval based on system activity
            idle_time = self._get_system_idle_time()
            if idle_time > 60:  # seconds
                # Reduce check frequency during idle periods
                self.timer.setFireDate_(NSDate.dateWithTimeIntervalSinceNow_(1.0))
            else:
                # Normal frequency during active use
                self.timer.setFireDate_(NSDate.dateWithTimeIntervalSinceNow_(CONFIG['enhanced_check_interval']))
            
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
                    
                    # Use performSelectorOnMainThread to show notification on main thread
                    if NSThread.isMainThread():
                        show_notification(CONFIG['notification_title'], "Clipboard changed (enhanced)!")
                    else:
                        # Schedule notification on main thread
                        NSApplication.sharedApplication().performSelectorOnMainThread_withObject_waitUntilDone_(
                            lambda: show_notification(CONFIG['notification_title'], "Clipboard changed (enhanced)!"),
                            None,
                            False
                        )

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

        def _get_system_idle_time(self):
            # Get system idle time in seconds
            try:
                idle_secs = subprocess.check_output(
                    ["/usr/sbin/ioreg", "-c", "IOHIDSystem"], 
                    universal_newlines=True
                )
                idle_match = re.search(r'"HIDIdleTime" = (\d+)', idle_secs)
                if idle_match:
                    return int(idle_match.group(1)) / 1000000000  # Convert to seconds
            except:
                pass
            return 0

def main():
    """Main entry point for the clipboard monitor."""
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
                # Check for pause flag
                pause_flag_path = os.path.expanduser("~/Library/Application Support/ClipboardMonitor/pause_flag")
                if os.path.exists(pause_flag_path):
                    # Service is paused, just sleep and continue
                    time.sleep(1)
                    continue
                
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
