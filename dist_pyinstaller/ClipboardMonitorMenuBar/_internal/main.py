import os
import importlib
import importlib.util # For module loading
import time
import pyperclip # Cross-platform clipboard library
import threading
import logging
from pathlib import Path
from utils import show_notification, safe_expanduser, get_clipboard_content, log_event, log_error
from clipboard_reader import ClipboardReader
from module_manager import ModuleManager
from config_manager import ConfigManager
from constants import (
    TIMER_INTERVAL_ACTIVE, TIMER_INTERVAL_IDLE, PAUSE_CHECK_INTERVAL,
    ERROR_RETRY_DELAY, PYPERCLIP_ERROR_DELAY, MAX_CONSECUTIVE_ERRORS,
    SYSTEM_IDLE_THRESHOLD, DEFAULT_MODULE_VALIDATION_TIMEOUT
)
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
    early_diag_path = paths.get("out_log", safe_expanduser("~/ClipboardMonitor_early_diag.log"))
    # Ensure log directory exists
    ensure_directory_exists(str(Path(early_diag_path).parent))
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
    log_file = Path(log_path)
    if not log_file.exists() or log_file.stat().st_size == 0:
        with log_file.open('a') as f:
            f.write(header)

LOG_HEADER = (
    f"=== Clipboard Monitor Output Log ===\n"
    f"Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    f"Format: [YYYY-MM-DD HH:MM:SS] [LEVEL ] | Message\n"
    f"-------------------------------------\n"
)

ERR_LOG_HEADER = (
    f"=== Clipboard Monitor Error Log ===\n"
    f"Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    f"Format: [YYYY-MM-DD HH:MM:SS] [LEVEL ] | Message\n"
    f"-------------------------------------\n"
)



# Initialize configuration manager
config_manager = ConfigManager()
CONFIG = config_manager.config

# Enable tracemalloc if requested in config
if CONFIG.get('performance', {}).get('enable_tracemalloc', False):
    tracemalloc.start()
    logger.info('tracemalloc started for memory profiling')

# Apply debug mode if enabled in config
if CONFIG.get('general', {}).get('debug_mode', False):
    logging.getLogger().setLevel(logging.DEBUG)
    for handler in logging.getLogger().handlers:
        handler.setLevel(logging.DEBUG)
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
        return self.module_manager.process_content(clipboard_content)

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
            # Check for pause flag first
            pause_flag_path = Path(safe_expanduser("~/Library/Application Support/ClipboardMonitor/pause_flag"))
            if pause_flag_path.exists():
                # Log this only in debug mode to avoid spamming logs.
                logger.debug("Service is paused via pause_flag. Skipping clipboard check.")
                return

            # Skip checks when system is idle
            if self.processing_in_progress:
                return
            
            # Adaptive checking interval based on system activity
            idle_time = self._get_system_idle_time()
            if idle_time > SYSTEM_IDLE_THRESHOLD:  # seconds
                # Reduce check frequency during idle periods
                self.timer.setFireDate_(NSDate.dateWithTimeIntervalSinceNow_(TIMER_INTERVAL_IDLE))
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
                            new_content = self.monitor_instance.process_clipboard(current_clipboard_content)
                            if new_content:
                                self.last_processed_clipboard_content = new_content
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
                # Create a timer that fires at the configured interval (much more responsive than polling)
                self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                    TIMER_INTERVAL_ACTIVE, self, objc.selector(self.checkClipboardChange_, signature=b'v@:@'), None, True
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
            except subprocess.SubprocessError:
                pass
            return 0

def print_tracemalloc_snapshot():
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        logger.info(f"[tracemalloc] Current memory usage: {current / 1024 / 1024:.2f} MB; Peak: {peak / 1024 / 1024:.2f} MB")

def _setup_monitor():
    """Setup and initialize the clipboard monitor."""
    log_event(f"Clipboard Monitor service starting... (out_log: {paths['out_log']}, err_log: {paths['err_log']})", level="INFO")
    logger.info(f"Clipboard Monitor service starting... (out_log: {paths['out_log']}, err_log: {paths['err_log']})")

    monitor = ClipboardMonitor()
    modules_dir = Path(__file__).parent / 'modules'
    monitor.load_modules(str(modules_dir))

    enabled_modules = monitor.module_manager.get_enabled_modules()
    if not enabled_modules:
        logger.warning("No modules enabled. Monitor will run but won't process clipboard content.")
    else:
        logger.info(f"Enabled modules: {', '.join(enabled_modules)}")
    
    return monitor


def _run_enhanced_monitoring(monitor):
    """Run enhanced clipboard monitoring using macOS pyobjc."""
    logger.info("Using enhanced clipboard monitoring (macOS).")

    initial_clipboard_content = None
    try:
        initial_clipboard_content = get_clipboard_content()
        if initial_clipboard_content:
            logger.info("Processing initial clipboard content (enhanced mode)...")
            monitor.process_clipboard(initial_clipboard_content)
    except Exception as e:
        logger.error(f"Error reading initial clipboard content (enhanced): {e}")

    try:
        app = NSApplication.sharedApplication()
        handler_instance = ClipboardMonitorHandler.alloc().initWithMonitor_andInitialContent_(monitor, initial_clipboard_content)
        handler_instance.startMonitoring()
        logger.info("Enhanced clipboard monitor started. Press Ctrl+C to exit.")

        try:
            app.run()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received in enhanced mode.")
        finally:
            if handler_instance:
                handler_instance.cleanup()

    except Exception as e:
        logger.error(f"Error setting up enhanced monitoring: {e}")
        logger.info("Falling back to polling mode...")
        return False
    else:
        logger.info("Enhanced clipboard monitor shut down.")
        return True


def _process_initial_clipboard_polling(monitor):
    """Process initial clipboard content for polling mode."""
    try:
        initial_clipboard_content = get_clipboard_content()
        if initial_clipboard_content:
            logger.info("Processing initial clipboard content (polling)...")
            log_event("Processing initial clipboard content (polling)...", level="INFO")
            monitor.process_clipboard(initial_clipboard_content)
            return initial_clipboard_content
    except Exception as e:
        logger.error(f"Error reading initial clipboard content (polling): {e}")
        log_error(f"Error reading initial clipboard content (polling): {e}")
    return None


def _handle_polling_iteration(monitor, last_clipboard, consecutive_errors, max_consecutive_errors):
    """Handle a single iteration of the polling loop."""
    try:
        # Check for pause flag
        pause_flag_path = Path(safe_expanduser("~/Library/Application Support/ClipboardMonitor/pause_flag"))
        if pause_flag_path.exists():
            log_event("Service paused via pause_flag.", level="INFO")
            time.sleep(PAUSE_CHECK_INTERVAL)
            return last_clipboard, consecutive_errors, True  # continue flag
        
        clipboard_content = get_clipboard_content()
        if clipboard_content and clipboard_content != last_clipboard:
            last_clipboard = clipboard_content
            log_event("Clipboard content changed (polling).", level="INFO")
            monitor.process_clipboard(clipboard_content)

        consecutive_errors = 0
        time.sleep(config_manager.get_polling_interval())
        return last_clipboard, consecutive_errors, True

    except pyperclip.PyperclipException as e:
        consecutive_errors += 1
        logger.error(f"pyperclip error in polling loop (#{consecutive_errors}): {e}")
        log_error(f"pyperclip error in polling loop (#{consecutive_errors}): {e}")

        if consecutive_errors >= max_consecutive_errors:
            logger.error(f"Too many consecutive pyperclip errors ({consecutive_errors}). Exiting.")
            log_error(f"Too many consecutive pyperclip errors ({consecutive_errors}). Exiting.")
            return last_clipboard, consecutive_errors, False

        time.sleep(PYPERCLIP_ERROR_DELAY)
        return last_clipboard, consecutive_errors, True

    except Exception as e:
        consecutive_errors += 1
        logger.error(f"Unexpected error in polling loop (#{consecutive_errors}): {e}")
        log_error(f"Unexpected error in polling loop (#{consecutive_errors}): {e}")

        if consecutive_errors >= max_consecutive_errors:
            logger.error(f"Too many consecutive errors ({consecutive_errors}). Exiting.")
            log_error(f"Too many consecutive errors ({consecutive_errors}). Exiting.")
            return last_clipboard, consecutive_errors, False

        time.sleep(ERROR_RETRY_DELAY)
        return last_clipboard, consecutive_errors, True


def _run_polling_monitoring(monitor):
    """Run polling-based clipboard monitoring."""
    logger.info("Clipboard monitor started (polling).")
    log_event("Clipboard monitor started (polling).", level="INFO")
    
    last_clipboard = _process_initial_clipboard_polling(monitor)
    consecutive_errors = 0
    max_consecutive_errors = MAX_CONSECUTIVE_ERRORS

    try:
        while True:
            last_clipboard, consecutive_errors, should_continue = _handle_polling_iteration(
                monitor, last_clipboard, consecutive_errors, max_consecutive_errors
            )
            if not should_continue:
                break

    except KeyboardInterrupt:
        logger.info("\nClipboard monitor stopped by user (polling).")
        log_event("Clipboard monitor stopped by user (polling).", level="INFO")
    except Exception as e:
        logger.error(f"Fatal error in polling loop: {e}")
        log_error(f"Fatal error in polling loop: {e}")
    finally:
        logger.info("Clipboard monitor shutdown complete.")
        log_event("Clipboard monitor shutdown complete.", level="INFO")


def main():
    """Main entry point for the clipboard monitor."""
    monitor = _setup_monitor()

    # Try enhanced monitoring first (macOS with pyobjc)
    if MACOS_ENHANCED:
        if _run_enhanced_monitoring(monitor):
            return

    # Fall back to polling monitoring
    _run_polling_monitoring(monitor)
# Standard Python entry point.
if __name__ == "__main__":
    main()
