import os
import importlib
import importlib.util # For module loading
import time
import pyperclip # Cross-platform clipboard library
import threading
import logging
from utils import show_notification, safe_expanduser, get_clipboard_content, log_event, log_error
from clipboard_reader import ClipboardReader
from module_manager import ModuleManager
from config_manager import ConfigManager
import json
import subprocess
import re # For regex in _get_system_idle_time
import tracemalloc


from utils import setup_logging, get_app_paths

# --- BEGIN: Early environment and log path diagnostics ---
try:
    import sys
    import datetime
    from utils import get_app_paths, ensure_directory_exists
    paths = get_app_paths()
    early_diag_path = paths.get("out_log", os.path.expanduser("~/ClipboardMonitor_early_diag.log"))
    # Ensure log directory exists
    ensure_directory_exists(os.path.dirname(early_diag_path))
    with open(early_diag_path, "a") as diag:
        diag.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Service starting. (early diagnostics)\n")
        diag.write(f"sys.argv: {sys.argv}\n")
        diag.write(f"os.getcwd(): {os.getcwd()}\n")
        diag.write(f"__file__: {__file__}\n")
        diag.write(f"os.environ['HOME']: {os.environ.get('HOME')}\n")
        diag.write(f"os.environ['USER']: {os.environ.get('USER')}\n")
        diag.write(f"PATH: {os.environ.get('PATH')}\n")
        # Try to resolve log file paths if possible
        try:
            diag.write(f"Resolved out_log: {paths.get('out_log')}\n")
            diag.write(f"Resolved err_log: {paths.get('err_log')}\n")
        except Exception as e:
            diag.write(f"Error resolving log paths: {e}\n")
        diag.write("---\n")
except Exception as e:
    pass
# --- END: Early environment and log path diagnostics ---

paths = get_app_paths()
setup_logging(paths["out_log"], paths["err_log"])
logger = logging.getLogger("clipboard_monitor")

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



# Initialize configuration manager
config_manager = ConfigManager()
CONFIG = config_manager.config

# Enable tracemalloc if requested in config
if CONFIG.get('performance', {}).get('enable_tracemalloc', False):
    tracemalloc.start()
    logger.info('tracemalloc started for memory profiling')

# Apply debug mode if enabled in config
if CONFIG.get('debug_mode', False):
    logging.getLogger().setLevel(logging.DEBUG)
    logger.info("Debug mode enabled")

# Attempt to import pyobjc for enhanced clipboard monitoring on macOS.
try:
    from AppKit import NSPasteboard, NSApplication, NSObject, NSThread
    from Foundation import NSTimer, NSDate
    import objc # For @objc.selector decorator
    MACOS_ENHANCED = True
    logger.debug("pyobjc loaded successfully. Enhanced monitoring enabled for macOS.")
except ImportError:
    # If pyobjc is not found, set a flag to fall back to polling.
    logger.warning("pyobjc not found. Falling back to polling clipboard monitoring.")
    logger.warning("For enhanced monitoring on macOS, install it: pip install pyobjc-framework-Cocoa")
    MACOS_ENHANCED = False

try:
    from AppKit import NSApplication, NSApplicationActivationPolicyProhibited
    NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyProhibited)
except Exception:
    pass



class ClipboardMonitor:
    """
    Orchestrates clipboard monitoring using separate reader and module manager components.
    """
    def __init__(self):
        """Initialize the clipboard monitor with its components."""
        self.clipboard_reader = ClipboardReader()
        self.module_manager = ModuleManager()

    def load_modules(self, modules_dir):
        """Load modules using the module manager."""
        self.module_manager.load_modules(modules_dir)

    def process_clipboard(self, clipboard_content) -> bool:
        """Process clipboard content using the module manager."""
        return self.module_manager.process_content(
            clipboard_content, 
            config_manager.get_max_clipboard_size()
        )

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
                self.timer.setFireDate_(NSDate.dateWithTimeIntervalSinceNow_(config_manager.get_enhanced_check_interval()))
            
            # Prevent recursive processing if a module modifies the clipboard
            if self.processing_in_progress:
                return

            current_change_count = self.pasteboard.changeCount()
            if current_change_count != self.last_change_count:
                self.last_change_count = current_change_count

                try:
                    # Try to get clipboard content, preferring text but also checking for RTF
                    current_clipboard_content = self._get_clipboard_content()
                    if current_clipboard_content is None:
                        logger.debug("No clipboard content available")
                        return
                except Exception as e:
                    logger.error(f"Error reading clipboard in timer handler: {e}")
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

                    logger.info("Clipboard changed (enhanced monitoring)!")

                    # If the monitor instance is available, process the new clipboard content.
                    if self.monitor_instance:
                        try:
                            self.monitor_instance.process_clipboard(current_clipboard_content)
                        except Exception as e:
                            # Log any errors during the processing by the modules.
                            logger.error(f"Error during monitor.process_clipboard from timer handler: {e}")
                    else:
                        logger.error("Monitor instance not available in ClipboardMonitorHandler")
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

        def _get_clipboard_content(self):
            """Get clipboard content using centralized utility function."""
            return get_clipboard_content()

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

def print_tracemalloc_snapshot():
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        logger.info(f"[tracemalloc] Current memory usage: {current / 1024 / 1024:.2f} MB; Peak: {peak / 1024 / 1024:.2f} MB")

def main():
    """Main entry point for the clipboard monitor."""
    # Log resolved log file paths and service start immediately
    log_event(f"Clipboard Monitor service starting... (out_log: {paths['out_log']}, err_log: {paths['err_log']})", level="INFO")
    logger.info(f"Clipboard Monitor service starting... (out_log: {paths['out_log']}, err_log: {paths['err_log']})")

    monitor = ClipboardMonitor()
    modules_dir = os.path.join(os.path.dirname(__file__), 'modules')
    monitor.load_modules(modules_dir)

    enabled_modules = monitor.module_manager.get_enabled_modules()
    if not enabled_modules:
        logger.warning("No modules enabled. Monitor will run but won't process clipboard content.")
    else:
        logger.info(f"Enabled modules: {', '.join(enabled_modules)}")

    # --- Enhanced Monitoring Path (macOS with pyobjc) ---
    if MACOS_ENHANCED:
        logger.info("Using enhanced clipboard monitoring (macOS).")

        initial_clipboard_content = None
        try:
            # Get the initial clipboard content when the script starts.
            initial_clipboard_content = get_clipboard_content()
            if initial_clipboard_content: # Only process if there's something initially
                logger.info("Processing initial clipboard content (enhanced mode)...")
                # Process this initial content once.
                monitor.process_clipboard(initial_clipboard_content)
        except Exception as e:
            logger.error(f"Error reading initial clipboard content (enhanced): {e}")

        try:
            app = NSApplication.sharedApplication() # Get a shared NSApplication instance
            # Create an instance of our monitor handler, passing the monitor and initial content.
            handler_instance = ClipboardMonitorHandler.alloc().initWithMonitor_andInitialContent_(monitor, initial_clipboard_content)

            # Start the timer-based monitoring
            handler_instance.startMonitoring()

            logger.info("Enhanced clipboard monitor started. Press Ctrl+C to exit.")

            try:
                app.run() # Start the Cocoa event loop. This call will block and keep the script running,
                          # with the timer checking for clipboard changes.
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received in enhanced mode.")
            finally:
                # Clean up the handler
                if handler_instance:
                    handler_instance.cleanup()

        except Exception as e:
            logger.error(f"Error setting up enhanced monitoring: {e}")
            logger.info("Falling back to polling mode...")
            # Fall through to polling mode
        else:
            # This line is unlikely to be reached if Ctrl+C terminates the app directly.
            logger.info("Enhanced clipboard monitor shut down.")
            return

    # --- Polling Monitoring Path (Fallback if pyobjc is not available or not on macOS) ---
    # This will also be reached if event-driven setup fails
    logger.info("Clipboard monitor started (polling).")
    log_event("Clipboard monitor started (polling).", level="INFO")
    last_clipboard = None
    consecutive_errors = 0
    max_consecutive_errors = 10

    try:
        # Process initial clipboard content for polling mode too
        initial_clipboard_content = get_clipboard_content()
        if initial_clipboard_content:
            logger.info("Processing initial clipboard content (polling)...")
            log_event("Processing initial clipboard content (polling)...", level="INFO")
            last_clipboard = initial_clipboard_content # Set for the first comparison
            monitor.process_clipboard(initial_clipboard_content)
    except Exception as e:
        logger.error(f"Error reading initial clipboard content (polling): {e}")
        log_error(f"Error reading initial clipboard content (polling): {e}")

    # Main polling loop.
    try:
        while True:
            try:
                # Check for pause flag
                pause_flag_path = safe_expanduser("~/Library/Application Support/ClipboardMonitor/pause_flag")
                if os.path.exists(pause_flag_path):
                    # Service is paused, just sleep and continue
                    log_event("Service paused via pause_flag.", level="INFO")
                    time.sleep(1)
                    continue
                
                clipboard_content = get_clipboard_content()
                # If the current clipboard content is different from the last known content.
                if clipboard_content and clipboard_content != last_clipboard:
                    last_clipboard = clipboard_content
                    log_event("Clipboard content changed (polling).", level="INFO")
                    monitor.process_clipboard(clipboard_content)

                # Reset error counter on successful iteration
                consecutive_errors = 0
                time.sleep(config_manager.get_polling_interval())  # Configurable polling interval

            except pyperclip.PyperclipException as e:
                consecutive_errors += 1
                logger.error(f"pyperclip error in polling loop (#{consecutive_errors}): {e}")
                log_error(f"pyperclip error in polling loop (#{consecutive_errors}): {e}")

                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"Too many consecutive pyperclip errors ({consecutive_errors}). Exiting.")
                    log_error(f"Too many consecutive pyperclip errors ({consecutive_errors}). Exiting.")
                    break

                time.sleep(5) # Wait longer if there's a persistent pyperclip issue to avoid spamming errors.

            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Unexpected error in polling loop (#{consecutive_errors}): {e}")
                log_error(f"Unexpected error in polling loop (#{consecutive_errors}): {e}")

                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"Too many consecutive errors ({consecutive_errors}). Exiting.")
                    log_error(f"Too many consecutive errors ({consecutive_errors}). Exiting.")
                    break

                time.sleep(1) # Brief pause before retrying

    except KeyboardInterrupt: # Handle Ctrl+C to gracefully stop the monitor.
        logger.info("\nClipboard monitor stopped by user (polling).")
        log_event("Clipboard monitor stopped by user (polling).", level="INFO")
    except Exception as e:
        logger.error(f"Fatal error in polling loop: {e}")
        log_error(f"Fatal error in polling loop: {e}")
    finally:
        logger.info("Clipboard monitor shutdown complete.")
        log_event("Clipboard monitor shutdown complete.", level="INFO")
# Standard Python entry point.
if __name__ == "__main__":
    main()
