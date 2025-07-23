#!/usr/bin/env python3
import rumps
import subprocess
import threading
import os
import sys
import webbrowser
import threading
import time
import json
import logging
from pathlib import Path
from utils import safe_expanduser, ensure_directory_exists, set_config_value, load_clipboard_history, setup_logging, get_app_paths, show_notification
from config_manager import ConfigManager
from constants import POLLING_INTERVALS, ENHANCED_CHECK_INTERVALS
# Optional import for pyperclip (may not be available in PyInstaller bundle)
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    pyperclip = None

# Hide Dock icon for menu bar app
try:
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
    NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
except Exception:
    pass

# Simple memory debugging
import psutil
import threading
import time
from datetime import datetime

MEMORY_DEBUG_AVAILABLE = True

def memory_profile_function(func):
    """Decorator to profile memory usage of functions."""
    def wrapper(*args, **kwargs):
        if not MEMORY_DEBUG_AVAILABLE:
            return func(*args, **kwargs)

        try:
            # Get memory before function execution
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024
            start_time = time.time()

            # Execute the function
            result = func(*args, **kwargs)

            # Get memory after function execution
            memory_after = process.memory_info().rss / 1024 / 1024
            execution_time = time.time() - start_time
            memory_delta = memory_after - memory_before

            # ALWAYS log profiled functions for debugging (no thresholds)
            log_memory(
                f"Execution time: {execution_time:.3f}s",
                level="INFO" if abs(memory_delta) < 2 else "WARNING",
                function_name=func.__name__,
                memory_delta=memory_delta
            )

            return result

        except Exception as e:
            log_memory(f"Error profiling function {func.__name__}: {e}", "ERROR")
            return func(*args, **kwargs)

    return wrapper

def log_memory(message, level="INFO", function_name=None, memory_delta=None):
    """Enhanced memory logging function with detailed debugging."""
    try:
        import gc
        import threading

        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        vms_mb = memory_info.vms / 1024 / 1024

        # Get additional system info
        cpu_percent = process.cpu_percent()
        thread_count = threading.active_count()
        gc_objects = len(gc.get_objects())

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build comprehensive log entry
        log_parts = [
            f"[{timestamp}] [{level}]",
            f"RSS: {memory_mb:.1f}MB",
            f"VMS: {vms_mb:.1f}MB",
            f"CPU: {cpu_percent:.1f}%",
            f"Threads: {thread_count}",
            f"Objects: {gc_objects}"
        ]

        if function_name:
            log_parts.append(f"Function: {function_name}")

        if memory_delta is not None:
            log_parts.append(f"Delta: {memory_delta:+.2f}MB")

        log_parts.append(f"| {message}")

        log_entry = " ".join(log_parts)

        with open("memory_leak_debug.log", "a") as f:
            f.write(log_entry + "\n")

        if level in ["WARNING", "ERROR"] or (memory_delta and abs(memory_delta) > 5):
            print(log_entry)

    except Exception as e:
        # Fallback to simple logging if enhanced logging fails
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        simple_entry = f"[{timestamp}] [ERROR] Memory logging failed: {e} | {message}"
        try:
            with open("memory_leak_debug.log", "a") as f:
                f.write(simple_entry + "\n")
        except:
            pass

def start_memory_monitoring():
    """Start enhanced memory monitoring with detailed analysis."""
    def monitor_loop():
        import gc
        baseline = None
        loop_count = 0
        previous_memory = None
        memory_samples = []

        while True:
            try:
                loop_count += 1
                process = psutil.Process()
                memory_info = process.memory_info()
                current_memory = memory_info.rss / 1024 / 1024

                # Collect garbage and get object counts
                gc.collect()
                object_count = len(gc.get_objects())

                if baseline is None:
                    baseline = current_memory
                    previous_memory = current_memory
                    log_memory(f"Baseline established", function_name="monitor_loop")

                increase_from_baseline = current_memory - baseline
                increase_from_previous = current_memory - previous_memory if previous_memory else 0

                # Store sample for trend analysis
                memory_samples.append({
                    'memory': current_memory,
                    'timestamp': time.time(),
                    'objects': object_count
                })

                # Keep only last 12 samples (1 hour of data)
                if len(memory_samples) > 12:
                    memory_samples.pop(0)

                # Calculate trend if we have enough samples
                trend_info = ""
                if len(memory_samples) >= 3:
                    recent_growth = memory_samples[-1]['memory'] - memory_samples[-3]['memory']
                    time_span = memory_samples[-1]['timestamp'] - memory_samples[-3]['timestamp']
                    if time_span > 0:
                        growth_rate = (recent_growth / (time_span / 3600))  # MB per hour
                        trend_info = f" Trend: {growth_rate:+.1f}MB/h"

                # Determine log level based on memory increase
                if increase_from_baseline > 100:
                    level = "ERROR"
                elif increase_from_baseline > 50:
                    level = "WARNING"
                elif abs(increase_from_previous) > 10:
                    level = "WARNING"
                else:
                    level = "INFO"

                # Log comprehensive memory status
                log_memory(
                    f"Check #{loop_count}: +{increase_from_baseline:+.1f}MB from baseline, "
                    f"{increase_from_previous:+.1f}MB from previous{trend_info}",
                    level=level,
                    function_name="monitor_loop"
                )

                # Additional analysis every 6 checks (30 minutes)
                if loop_count % 6 == 0 and len(memory_samples) >= 6:
                    oldest_sample = memory_samples[0]
                    newest_sample = memory_samples[-1]
                    total_growth = newest_sample['memory'] - oldest_sample['memory']
                    object_growth = newest_sample['objects'] - oldest_sample['objects']
                    time_span = newest_sample['timestamp'] - oldest_sample['timestamp']

                    if time_span > 0:
                        hourly_growth = (total_growth / (time_span / 3600))
                        log_memory(
                            f"30min analysis: {total_growth:+.1f}MB growth, "
                            f"{object_growth:+d} objects, rate: {hourly_growth:+.1f}MB/h",
                            level="WARNING" if hourly_growth > 20 else "INFO",
                            function_name="monitor_analysis"
                        )

                previous_memory = current_memory

            except Exception as e:
                log_memory(f"Error in monitoring loop #{loop_count}: {e}", "ERROR")

            time.sleep(300)  # Check every 5 minutes

    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    log_memory("Enhanced memory monitoring started", function_name="start_memory_monitoring")




class ClipboardMonitorMenuBar(rumps.App):
    def __init__(self):
        # Use a simple title with an emoji that works in the menu bar
        super().__init__("📋", quit_button=None)

        # Configuration
        self.config_manager = ConfigManager()
        self.home_dir = str(Path.home())
        # Use development service plist if it exists, otherwise use production
        dev_plist = f"{self.home_dir}/Library/LaunchAgents/com.clipboardmonitor.service.dev.plist"
        prod_plist = f"{self.home_dir}/Library/LaunchAgents/com.clipboardmonitor.plist"
        self.plist_path = dev_plist if os.path.exists(dev_plist) else prod_plist
        # Use separate log files for menu bar app to avoid permission conflicts
        log_dir = Path.home() / "Library" / "Logs"
        self.log_path = str(log_dir / "ClipboardMonitorMenuBar.out.log")
        self.error_log_path = str(log_dir / "ClipboardMonitorMenuBar.err.log")
        setup_logging(self.log_path, self.error_log_path)
        self.module_status = {}
        self.load_module_config()
        # Map of module filenames to friendly display names
        self.module_display_names = {
            "markdown_module": "Markdown Processor",
            "mermaid_module": "Mermaid Diagram Detector",
            "drawio_module": "Draw.io Diagram Detector",
            "history_module": "Clipboard History Tracker",
            "code_formatter_module": "Code Formatter"
        }

        # Initialize polling options
        self.polling_options = POLLING_INTERVALS
        self.enhanced_options = ENHANCED_CHECK_INTERVALS

        # Initialize menu components
        self._init_menu_items()
        self._init_submenus()
        self._init_preferences_menu()

        # Initialize menu item storage for all radio-button style menus
        self.mermaid_theme_items = {}
        self.drawio_edit_mode_items = {}
        self.drawio_appearance_items = {}
        self.drawio_link_behavior_items = {}
        self.enhanced_interval_items = {}
        self.polling_interval_items = {}

        # Build the main menu structure
        self._build_main_menu()

        # Schedule initial history update and periodic status checks
        # Use a threading timer for one-time initial history update
        def delayed_history_setup():
            time.sleep(3)
            self.update_recent_history_menu()
            # Set up periodic updates using rumps Timer (runs on main thread)
            self.history_timer = rumps.Timer(self.periodic_history_update, 30)
            self.history_timer.start()
            log_memory("History timer started", "INFO")

        history_setup_thread = threading.Thread(target=delayed_history_setup, daemon=True)
        history_setup_thread.start()
        self.timer = threading.Thread(target=self.update_status_periodically)
        self.timer.daemon = True
        self.timer.start()

        # Start memory monitoring
        self.memory_timer = rumps.Timer(self.update_memory_status, 5)
        self.memory_timer.start()

        # Activate memory debugging
        if MEMORY_DEBUG_AVAILABLE:
            start_memory_monitoring()
            log_memory("Menu bar app initialized with memory debugging")

    def set_config_and_reload(self, section, key, value):
        """Set a configuration value and reload the config manager to pick up changes."""
        success = set_config_value(section, key, value)
        if success:
            self.config_manager.reload()
        return success

    def _init_menu_items(self):
        """Initialize individual menu items."""
        self.status_item = rumps.MenuItem("Status: Checking...")
        self.pause_toggle = rumps.MenuItem("Pause Monitoring", callback=self.toggle_monitoring)
        self.start_item = rumps.MenuItem("Start Service", callback=self.start_service)
        self.stop_item = rumps.MenuItem("Stop Service", callback=self.stop_service)
        self.restart_item = rumps.MenuItem("Restart Service", callback=self.restart_service)
        self.output_log_item = rumps.MenuItem("View Output Log", callback=self.view_output_log)
        self.error_log_item = rumps.MenuItem("View Error Log", callback=self.view_error_log)
        self.clear_logs_item = rumps.MenuItem("Clear Logs", callback=self.clear_logs)
        self.quit_item = rumps.MenuItem("Quit", callback=self.quit_app)
        self.history_menu = rumps.MenuItem("View Clipboard History")
        self.recent_history_menu = rumps.MenuItem("Recent Clipboard Items")
        self.prefs_menu = rumps.MenuItem("Preferences")
        self.module_menu = rumps.MenuItem("Modules")

        # Memory visualization display items for main menu (two lines)
        self.memory_menubar_item = rumps.MenuItem("Menu Bar: Initializing...")
        self.memory_service_item = rumps.MenuItem("Service: Initializing...")

        # Unified Memory Dashboard (moved to root menu)
        self.memory_unified_dashboard_item = rumps.MenuItem("📊 Unified Dashboard", callback=self.start_unified_dashboard)

        # Initialize monitoring processes tracking
        self._monitoring_processes = {}

        # Auto-start unified dashboard on app launch
        with open('/tmp/clipboard_debug.log', 'a') as f:
            f.write(f"DEBUG: About to call _auto_start_dashboard from __init__ at {time.time()}\n")
        self._auto_start_dashboard()

        # Mini histogram data for menu display
        self.menubar_history = []
        self.service_history = []
        self.menubar_peak = 0
        self.service_peak = 0



    def _init_submenus(self):
        """Initialize and populate submenus."""
        # Service Control Submenu
        self.service_control_menu = rumps.MenuItem("Service Control")
        self.service_control_menu.add(self.start_item)
        self.service_control_menu.add(self.stop_item)
        self.service_control_menu.add(self.restart_item)

        # Logs Submenu
        self.logs_menu = rumps.MenuItem("Logs")
        self.logs_menu.add(self.output_log_item)
        self.logs_menu.add(self.error_log_item)
        self.logs_menu.add(self.clear_logs_item)

        # Module Management Submenu
        self._populate_module_menu()

        # History Viewer Submenu
        self._populate_history_viewer_menu()

        # Recent History Submenu (initial state)
        self.recent_history_menu.add(rumps.MenuItem("🔄 Loading history...", callback=None))

    def _populate_module_menu(self):
        """Dynamically load and add modules to the module menu, including Draw.io."""
        modules_dir = os.path.join(os.path.dirname(__file__), 'modules')
        if os.path.exists(modules_dir):
            for filename in os.listdir(modules_dir):
                if filename.endswith('_module.py'):
                    module_name = filename[:-3]
                    display_name = self.module_display_names.get(module_name, module_name)
                    module_item = rumps.MenuItem(display_name)
                    config_value = self.module_status.get(module_name, True)
                    module_item.state = config_value not in [0, False]
                    module_item._module_name = module_name
                    module_item.set_callback(self.toggle_module)
                    self.module_menu.add(module_item)
                    if module_name not in self.module_status:
                        self.module_status[module_name] = True

        # Add configuration entry for Draw.io if not present
        if "drawio_module" not in self.module_status:
            self.module_status["drawio_module"] = True
        
    def toggle_drawio_setting(self, sender):
        """Toggle Draw.io specific settings."""
        sender.state = not sender.state

        setting_map = {
            "Copy Code": "drawio_copy_code",
            "Copy URL": "drawio_copy_url",
            "Open in Browser": "drawio_open_in_browser"
        }

        config_key = setting_map.get(sender.title)
        if config_key:
            if set_config_value('modules', config_key, sender.state):
                rumps.notification("Clipboard Monitor", "Draw.io Setting",
                                  f"{sender.title} is now {'enabled' if sender.state else 'disabled'}")
                self.restart_service(None)
            else:
                rumps.notification("Error", "Failed to update Draw.io setting", "Could not save configuration")

    def toggle_drawio_url_parameter(self, sender):
        """Toggle Draw.io URL parameter settings."""
        sender.state = not sender.state

        setting_map = {
            "Lightbox": "drawio_lightbox",
            "Layers Enabled": "drawio_layers",
            "Navigation Enabled": "drawio_nav"
        }

        config_key = setting_map.get(sender.title)
        if config_key:
            if set_config_value('modules', config_key, sender.state):
                rumps.notification("Clipboard Monitor", "Draw.io URL Parameter",
                                  f"{sender.title} is now {'enabled' if sender.state else 'disabled'}")
                self.restart_service(None)
            else:
                rumps.notification("Error", "Failed to update Draw.io URL parameter", "Could not save configuration")

    def set_drawio_edit_mode(self, sender):
        """Set Draw.io edit mode."""
        print(f"DEBUG: Setting Draw.io edit mode to {sender.title}")

        # Update all menu item states using stored references
        for item_name, item in self.drawio_edit_mode_items.items():
            old_state = item.state
            item.state = (item_name == sender.title)
            print(f"DEBUG: Draw.io edit mode '{item_name}' state: {old_state} -> {item.state}")

        mode_map = {"New Tab": "_blank", "Same Tab": "_self"}
        new_mode = mode_map[sender.title]
        print(f"DEBUG: Mapped edit mode: {new_mode}")

        if self.set_config_and_reload('modules', 'drawio_edit_mode', new_mode):
            print(f"DEBUG: Successfully saved Draw.io edit mode {new_mode}")
            rumps.notification("Clipboard Monitor", "Draw.io Edit Mode",
                              f"Edit mode set to {sender.title}")
            self.restart_service(None)
        else:
            print(f"DEBUG: Failed to save Draw.io edit mode {new_mode}")
            rumps.notification("Error", "Failed to update Draw.io edit mode", "Could not save configuration")

    def set_drawio_appearance(self, sender):
        """Set Draw.io appearance."""
        print(f"DEBUG: Setting Draw.io appearance to {sender.title}")

        # Update all menu item states using stored references
        for item_name, item in self.drawio_appearance_items.items():
            old_state = item.state
            item.state = (item_name == sender.title)
            print(f"DEBUG: Draw.io appearance '{item_name}' state: {old_state} -> {item.state}")

        appearance_map = {"Auto": "auto", "Light": "light", "Dark": "dark"}
        new_appearance = appearance_map[sender.title]
        print(f"DEBUG: Mapped appearance: {new_appearance}")

        if self.set_config_and_reload('modules', 'drawio_appearance', new_appearance):
            print(f"DEBUG: Successfully saved Draw.io appearance {new_appearance}")
            rumps.notification("Clipboard Monitor", "Draw.io Appearance",
                              f"Appearance set to {sender.title}")
            self.restart_service(None)
        else:
            print(f"DEBUG: Failed to save Draw.io appearance {new_appearance}")
            rumps.notification("Error", "Failed to update Draw.io appearance", "Could not save configuration")

    def set_drawio_link_behavior(self, sender):
        """Set Draw.io link behavior."""
        print(f"DEBUG: Setting Draw.io link behavior to {sender.title}")

        # Update all menu item states using stored references
        for item_name, item in self.drawio_link_behavior_items.items():
            old_state = item.state
            item.state = (item_name == sender.title)
            print(f"DEBUG: Draw.io link behavior '{item_name}' state: {old_state} -> {item.state}")

        behavior_map = {"Auto": "auto", "New Tab": "blank", "Same Tab": "self"}
        new_behavior = behavior_map[sender.title]
        print(f"DEBUG: Mapped link behavior: {new_behavior}")

        if self.set_config_and_reload('modules', 'drawio_links', new_behavior):
            print(f"DEBUG: Successfully saved Draw.io link behavior {new_behavior}")
            rumps.notification("Clipboard Monitor", "Draw.io Link Behavior",
                              f"Link behavior set to {sender.title}")
            self.restart_service(None)
        else:
            print(f"DEBUG: Failed to save Draw.io link behavior {new_behavior}")
            rumps.notification("Error", "Failed to update Draw.io link behavior", "Could not save configuration")

    def set_drawio_border_color(self, _):
        """Set Draw.io border color."""
        current_color = self.config_manager.get_config_value('modules', 'drawio_border_color', '#000000')
        response = rumps.Window(
            message="Enter border color (hex format, e.g., #FF0000):",
            title="Set Draw.io Border Color",
            default_text=current_color,
            ok="Set",
            cancel="Cancel",
            dimensions=(300, 20)
        ).run()

        if response.clicked and response.text.strip():
            color = response.text.strip()
            # Basic validation for hex color
            if color.startswith('#') and len(color) == 7:
                if set_config_value('modules', 'drawio_border_color', color):
                    rumps.notification("Clipboard Monitor", "Draw.io Border Color",
                                      f"Border color set to {color}")
                    self.restart_service(None)
                else:
                    rumps.notification("Error", "Failed to update Draw.io border color", "Could not save configuration")
            else:
                rumps.notification("Error", "Invalid Color Format", "Please use hex format like #FF0000")

    def _populate_history_viewer_menu(self):
        """Populate the 'View Clipboard History' submenu."""
        self.history_menu.add(rumps.MenuItem("Open in Browser", callback=self.open_web_history_viewer))
        self.history_menu.add(rumps.MenuItem("Open in Terminal", callback=self.open_cli_history_viewer))
        self.history_menu.add(rumps.separator)
        self.history_menu.add(rumps.MenuItem("🗑️ Clear History", callback=self.clear_clipboard_history))

    def _create_polling_interval_menu(self):
        """Create the 'Polling Interval' submenu."""
        polling_menu = rumps.MenuItem("Polling Interval")
        current_polling = self.config_manager.get_config_value('general', 'polling_interval', 1.0)
        print(f"DEBUG: Creating polling interval menu, current interval: {current_polling}")

        # Clear previous polling interval items
        self.polling_interval_items = {}

        for name, value in self.polling_options.items():
            item = rumps.MenuItem(name, callback=self.set_polling_interval)
            item.state = (value == current_polling)
            polling_menu.add(item)

            # Store reference to the item for later state updates
            self.polling_interval_items[name] = item

            print(f"DEBUG: Added polling interval item '{name}' (value: {value}), state: {item.state}")

        return polling_menu

    def _create_enhanced_interval_menu(self):
        """Create the 'Enhanced Check Interval' submenu."""
        enhanced_menu = rumps.MenuItem("Enhanced Check Interval")
        current_enhanced = self.config_manager.get_config_value('general', 'enhanced_check_interval', 0.1)
        print(f"DEBUG: Creating enhanced check interval menu, current interval: {current_enhanced}")

        # Clear previous enhanced interval items
        self.enhanced_interval_items = {}

        for name, value in self.enhanced_options.items():
            item = rumps.MenuItem(name, callback=self.set_enhanced_interval)
            item.state = (value == current_enhanced)
            enhanced_menu.add(item)

            # Store reference to the item for later state updates
            self.enhanced_interval_items[name] = item

            print(f"DEBUG: Added enhanced interval item '{name}' (value: {value}), state: {item.state}")

        return enhanced_menu

    def _create_general_settings_menu(self):
        """Create the 'General Settings' submenu."""
        general_menu = rumps.MenuItem("General Settings")
        self.debug_mode = rumps.MenuItem("Debug Mode", callback=self.toggle_debug)
        self.debug_mode.state = self.config_manager.get_config_value('general', 'debug_mode', False)
        general_menu.add(self.debug_mode)
        general_menu.add(rumps.MenuItem("Set Notification Title...", callback=self.set_notification_title))
        general_menu.add(self._create_polling_interval_menu())
        general_menu.add(self._create_enhanced_interval_menu())
        return general_menu

    def _create_history_settings_menu(self):
        """Create the 'History Settings' submenu."""
        history_menu = rumps.MenuItem("History Settings")
        history_menu.add(rumps.MenuItem("Set Max History Items...", callback=self.set_max_history_items))
        history_menu.add(rumps.MenuItem("Set Max Content Length...", callback=self.set_max_content_length))
        history_menu.add(rumps.MenuItem("Set History Location...", callback=self.set_history_location))
        return history_menu

    def _create_clipboard_modification_menu(self):
        """Create the 'Clipboard Modification' submenu."""
        clipboard_menu = rumps.MenuItem("Clipboard Modification")
        self.markdown_modify = rumps.MenuItem("Markdown Modify Clipboard", callback=self.toggle_clipboard_modification)
        self.markdown_modify.state = self.config_manager.get_config_value('modules', 'markdown_modify_clipboard', True)
        clipboard_menu.add(self.markdown_modify)
        self.code_formatter_modify = rumps.MenuItem("Code Formatter Modify Clipboard", callback=self.toggle_clipboard_modification)
        self.code_formatter_modify.state = self.config_manager.get_config_value('modules', 'code_formatter_modify_clipboard', False)
        clipboard_menu.add(self.code_formatter_modify)
        return clipboard_menu

    def _create_drawio_settings_menu(self):
        """Create the 'Draw.io Settings' submenu."""
        # Copy Code option (restored)
        self.drawio_copy_code_item = rumps.MenuItem("✅ Copy Code", callback=self.toggle_drawio_setting)
        self.drawio_copy_code_item.state = self.config_manager.get_config_value('modules', 'drawio_copy_code', True)

        # Copy URL option
        self.drawio_copy_url_item = rumps.MenuItem("✅ Copy URL", callback=self.toggle_drawio_setting)
        self.drawio_copy_url_item.state = self.config_manager.get_config_value('modules', 'drawio_copy_url', True)

        # Open in Browser option
        self.drawio_open_browser_item = rumps.MenuItem("✅ Open in Browser", callback=self.toggle_drawio_setting)
        self.drawio_open_browser_item.state = self.config_manager.get_config_value('modules', 'drawio_open_in_browser', True)

        # URL Parameters submenu (restored)
        url_params_menu = self._create_drawio_url_parameters_menu()

        # Create a container menu to hold all settings
        settings_container = rumps.MenuItem("Settings")
        settings_container.add(self.drawio_copy_code_item)
        settings_container.add(self.drawio_copy_url_item)
        settings_container.add(self.drawio_open_browser_item)
        settings_container.add(rumps.separator)
        settings_container.add(url_params_menu)

        return settings_container

    def _create_drawio_settings_content(self):
        """Create Draw.io settings content as a list of menu items (no container)."""
        # Copy Code option
        self.drawio_copy_code_item = rumps.MenuItem("✅ Copy Code", callback=self.toggle_drawio_setting)
        self.drawio_copy_code_item.state = self.config_manager.get_config_value('modules', 'drawio_copy_code', True)

        # Copy URL option
        self.drawio_copy_url_item = rumps.MenuItem("✅ Copy URL", callback=self.toggle_drawio_setting)
        self.drawio_copy_url_item.state = self.config_manager.get_config_value('modules', 'drawio_copy_url', True)

        # Open in Browser option
        self.drawio_open_browser_item = rumps.MenuItem("✅ Open in Browser", callback=self.toggle_drawio_setting)
        self.drawio_open_browser_item.state = self.config_manager.get_config_value('modules', 'drawio_open_in_browser', True)

        # URL Parameters submenu
        url_params_menu = self._create_drawio_url_parameters_menu()

        # Return list of items
        return [
            self.drawio_copy_code_item,
            self.drawio_copy_url_item,
            self.drawio_open_browser_item,
            rumps.separator,
            url_params_menu
        ]

    def _create_drawio_url_parameters_menu(self):
        """Create the 'URL Parameters' submenu for Draw.io."""
        url_params_menu = rumps.MenuItem("URL Parameters")

        # Lightbox toggle
        self.drawio_lightbox_item = rumps.MenuItem("Lightbox", callback=self.toggle_drawio_url_parameter)
        self.drawio_lightbox_item.state = self.config_manager.get_config_value('modules', 'drawio_lightbox', True)
        url_params_menu.add(self.drawio_lightbox_item)

        # Edit Mode submenu
        url_params_menu.add(self._create_drawio_edit_mode_menu())

        # Layers Enabled toggle
        self.drawio_layers_item = rumps.MenuItem("Layers Enabled", callback=self.toggle_drawio_url_parameter)
        self.drawio_layers_item.state = self.config_manager.get_config_value('modules', 'drawio_layers', True)
        url_params_menu.add(self.drawio_layers_item)

        # Navigation Enabled toggle
        self.drawio_nav_item = rumps.MenuItem("Navigation Enabled", callback=self.toggle_drawio_url_parameter)
        self.drawio_nav_item.state = self.config_manager.get_config_value('modules', 'drawio_nav', True)
        url_params_menu.add(self.drawio_nav_item)

        # Appearance submenu
        url_params_menu.add(self._create_drawio_appearance_menu())

        # Link Behavior submenu
        url_params_menu.add(self._create_drawio_link_behavior_menu())

        # Border Color setting
        url_params_menu.add(rumps.MenuItem("Set Border Color...", callback=self.set_drawio_border_color))

        return url_params_menu

    def _create_drawio_edit_mode_menu(self):
        """Create the 'Edit Mode' submenu for Draw.io."""
        edit_mode_menu = rumps.MenuItem("Edit Mode")
        current_mode = self.config_manager.get_config_value('modules', 'drawio_edit_mode', '_blank')
        print(f"DEBUG: Creating Draw.io edit mode menu, current mode: {current_mode}")

        # Clear previous edit mode items
        self.drawio_edit_mode_items = {}

        modes = [("New Tab", "_blank"), ("Same Tab", "_self")]
        for name, value in modes:
            item = rumps.MenuItem(name, callback=self.set_drawio_edit_mode)
            item.state = (value == current_mode)
            edit_mode_menu.add(item)

            # Store reference to the item for later state updates
            self.drawio_edit_mode_items[name] = item

            print(f"DEBUG: Added Draw.io edit mode item '{name}' (value: {value}), state: {item.state}")

        return edit_mode_menu

    def _create_drawio_appearance_menu(self):
        """Create the 'Appearance' submenu for Draw.io."""
        appearance_menu = rumps.MenuItem("Appearance")
        current_appearance = self.config_manager.get_config_value('modules', 'drawio_appearance', 'auto')
        print(f"DEBUG: Creating Draw.io appearance menu, current appearance: {current_appearance}")

        # Clear previous appearance items
        self.drawio_appearance_items = {}

        appearances = [("Auto", "auto"), ("Light", "light"), ("Dark", "dark")]
        for name, value in appearances:
            item = rumps.MenuItem(name, callback=self.set_drawio_appearance)
            item.state = (value == current_appearance)
            appearance_menu.add(item)

            # Store reference to the item for later state updates
            self.drawio_appearance_items[name] = item

            print(f"DEBUG: Added Draw.io appearance item '{name}' (value: {value}), state: {item.state}")

        return appearance_menu

    def _create_drawio_link_behavior_menu(self):
        """Create the 'Link Behavior' submenu for Draw.io."""
        link_menu = rumps.MenuItem("Link Behavior")
        current_behavior = self.config_manager.get_config_value('modules', 'drawio_links', 'auto')
        print(f"DEBUG: Creating Draw.io link behavior menu, current behavior: {current_behavior}")

        # Clear previous link behavior items
        self.drawio_link_behavior_items = {}

        behaviors = [("Auto", "auto"), ("New Tab", "blank"), ("Same Tab", "self")]
        for name, value in behaviors:
            item = rumps.MenuItem(name, callback=self.set_drawio_link_behavior)
            item.state = (value == current_behavior)
            link_menu.add(item)

            # Store reference to the item for later state updates
            self.drawio_link_behavior_items[name] = item

            print(f"DEBUG: Added Draw.io link behavior item '{name}' (value: {value}), state: {item.state}")

        return link_menu

    def _create_mermaid_settings_menu(self):
        """Create the 'Mermaid Settings' submenu."""
        # Copy Code option (restored)
        self.mermaid_copy_code_item = rumps.MenuItem("✅ Copy Code", callback=self.toggle_mermaid_setting)
        self.mermaid_copy_code_item.state = self.config_manager.get_config_value('modules', 'mermaid_copy_code', True)

        # Copy URL option
        self.mermaid_copy_url_item = rumps.MenuItem("❌ Copy URL", callback=self.toggle_mermaid_setting)
        self.mermaid_copy_url_item.state = self.config_manager.get_config_value('modules', 'mermaid_copy_url', False)

        # Open in Browser option (restored)
        self.mermaid_open_browser_item = rumps.MenuItem("✅ Open in Browser", callback=self.toggle_mermaid_setting)
        self.mermaid_open_browser_item.state = self.config_manager.get_config_value('modules', 'mermaid_open_in_browser', True)

        # Editor Theme submenu (restored)
        theme_menu = self._create_mermaid_editor_theme_menu()

        # Create a container menu to hold all settings
        settings_container = rumps.MenuItem("Settings")
        settings_container.add(self.mermaid_copy_code_item)
        settings_container.add(self.mermaid_copy_url_item)
        settings_container.add(self.mermaid_open_browser_item)
        settings_container.add(rumps.separator)
        settings_container.add(theme_menu)

        return settings_container

    def _create_mermaid_settings_content(self):
        """Create Mermaid settings content as a list of menu items (no container)."""
        # Copy Code option
        self.mermaid_copy_code_item = rumps.MenuItem("✅ Copy Code", callback=self.toggle_mermaid_setting)
        self.mermaid_copy_code_item.state = self.config_manager.get_config_value('modules', 'mermaid_copy_code', True)

        # Copy URL option
        self.mermaid_copy_url_item = rumps.MenuItem("❌ Copy URL", callback=self.toggle_mermaid_setting)
        self.mermaid_copy_url_item.state = self.config_manager.get_config_value('modules', 'mermaid_copy_url', False)

        # Open in Browser option
        self.mermaid_open_browser_item = rumps.MenuItem("✅ Open in Browser", callback=self.toggle_mermaid_setting)
        self.mermaid_open_browser_item.state = self.config_manager.get_config_value('modules', 'mermaid_open_in_browser', True)

        # Editor Theme submenu
        theme_menu = self._create_mermaid_editor_theme_menu()

        # Return list of items
        return [
            self.mermaid_copy_code_item,
            self.mermaid_copy_url_item,
            self.mermaid_open_browser_item,
            rumps.separator,
            theme_menu
        ]

    def _create_mermaid_editor_theme_menu(self):
        """Create the 'Editor Theme' submenu for Mermaid."""
        theme_menu = rumps.MenuItem("Editor Theme")
        current_theme = self.config_manager.get_config_value('modules', 'mermaid_editor_theme', 'default')
        print(f"DEBUG: Creating theme menu, current theme: {current_theme}")

        # Clear previous theme items
        self.mermaid_theme_items = {}

        themes = [("Default", "default"), ("Dark", "dark"), ("Forest", "forest"), ("Neutral", "neutral")]
        for name, value in themes:
            item = rumps.MenuItem(name, callback=self.set_mermaid_editor_theme)
            item.state = (value == current_theme)
            theme_menu.add(item)

            # Store reference to the item for later state updates
            self.mermaid_theme_items[name] = item

            print(f"DEBUG: Added theme item '{name}' (value: {value}), state: {item.state}, callback: {item.callback}")

        return theme_menu

    def _create_module_settings_menu(self):
        """Create the 'Module Settings' submenu."""
        module_menu = rumps.MenuItem("Module Settings")
        # Clipboard Modification moved to Security Settings
        module_menu.add(self._create_drawio_settings_menu())
        module_menu.add(self._create_mermaid_settings_menu())
        return module_menu

    def _create_performance_settings_menu(self):
        """Create the 'Performance Settings' submenu."""
        perf_menu = rumps.MenuItem("Performance Settings")
        self.lazy_loading = rumps.MenuItem("Lazy Module Loading", callback=self.toggle_performance_setting)
        self.lazy_loading.state = self.config_manager.get_config_value('performance', 'lazy_module_loading', True)
        perf_menu.add(self.lazy_loading)
        self.adaptive_checking = rumps.MenuItem("Adaptive Checking", callback=self.toggle_performance_setting)
        self.adaptive_checking.state = self.config_manager.get_config_value('performance', 'adaptive_checking', True)
        perf_menu.add(self.adaptive_checking)
        self.process_large_content = rumps.MenuItem("Process Large Content", callback=self.toggle_performance_setting)
        self.process_large_content.state = self.config_manager.get_config_value('performance', 'process_large_content', True)
        perf_menu.add(self.process_large_content)
        # Memory-related settings moved to dedicated Memory Settings menu
        perf_menu.add(rumps.MenuItem("Set Max Execution Time...", callback=self.set_max_execution_time))
        return perf_menu

    def _create_security_settings_menu(self):
        """Create the 'Security Settings' submenu."""
        security_menu = rumps.MenuItem("Security Settings")
        self.sanitize_clipboard = rumps.MenuItem("Sanitize Clipboard", callback=self.toggle_security_setting)
        self.sanitize_clipboard.state = self.config_manager.get_config_value('security', 'sanitize_clipboard', True)
        security_menu.add(self.sanitize_clipboard)
        security_menu.add(rumps.MenuItem("Set Max Clipboard Size...", callback=self.set_max_clipboard_size))

        # Clipboard Modification submenu (relocated from Module Settings)
        security_menu.add(rumps.separator)
        security_menu.add(self._create_clipboard_modification_menu())

        return security_menu

    def _create_configuration_management_menu(self):
        """Create the 'Configuration' submenu."""
        config_menu = rumps.MenuItem("Configuration")
        config_menu.add(rumps.MenuItem("Reset to Defaults", callback=self.reset_config_to_defaults))
        config_menu.add(rumps.MenuItem("Export Configuration...", callback=self.export_configuration))
        config_menu.add(rumps.MenuItem("Import Configuration...", callback=self.import_configuration))
        config_menu.add(rumps.MenuItem("View Current Configuration", callback=self.view_current_configuration))
        return config_menu

    def _create_advanced_settings_menu(self):
        """Create the 'Advanced Settings' submenu."""
        advanced_menu = rumps.MenuItem("Advanced Settings")
        advanced_menu.add(self._create_performance_settings_menu())  # Corrected method name
        advanced_menu.add(self._create_security_settings_menu())
        advanced_menu.add(self._create_configuration_management_menu())
        advanced_menu.add(rumps.separator)
        advanced_menu.add(self._create_memory_settings_menu())
        return advanced_menu

    def _create_memory_settings_menu(self):
        """Create the 'Memory Settings' submenu."""
        memory_menu = rumps.MenuItem("Memory Settings")

        # Unified Memory Dashboard (replaces separate visualizer and monitoring dashboard)
        memory_menu.add(rumps.MenuItem("📊 Unified Memory Dashboard", callback=self.start_unified_dashboard))

        memory_menu.add(rumps.separator)

        # Memory Optimization (moved from Performance Settings)
        self.memory_optimization_adv = rumps.MenuItem("Memory Optimization", callback=self.toggle_memory_setting)
        self.memory_optimization_adv.state = self.config_manager.get_config_value('performance', 'memory_optimization', True)
        memory_menu.add(self.memory_optimization_adv)

        # Memory Logging (moved from Performance Settings)
        self.memory_logging_adv = rumps.MenuItem("Memory Logging", callback=self.toggle_memory_setting)
        self.memory_logging_adv.state = self.config_manager.get_config_value('performance', 'memory_logging', True)
        memory_menu.add(self.memory_logging_adv)

        # Auto Memory Cleanup (new option)
        self.auto_memory_cleanup = rumps.MenuItem("Auto Memory Cleanup", callback=self.toggle_memory_setting)
        self.auto_memory_cleanup.state = self.config_manager.get_config_value('memory', 'auto_cleanup', False)
        memory_menu.add(self.auto_memory_cleanup)

        # Memory Leak Detection (new option)
        self.memory_leak_detection = rumps.MenuItem("Memory Leak Detection", callback=self.toggle_memory_setting)
        self.memory_leak_detection.state = self.config_manager.get_config_value('memory', 'leak_detection', True)
        memory_menu.add(self.memory_leak_detection)



        return memory_menu

    def _init_preferences_menu(self):
        """Initialize and populate the Preferences submenu."""
        self.prefs_menu.add(self._create_general_settings_menu())
        self.prefs_menu.add(self._create_history_settings_menu())
        self.prefs_menu.add(self._create_module_settings_menu())
        self.prefs_menu.add(self._create_advanced_settings_menu())

    def toggle_mermaid_setting(self, sender):
        """Toggle Mermaid specific settings."""
        sender.state = not sender.state

        setting_map = {
            "Copy Code": "mermaid_copy_code",
            "Copy URL": "mermaid_copy_url",
            "Open in Browser": "mermaid_open_in_browser"
        }

        config_key = setting_map.get(sender.title)
        if config_key:
            if set_config_value('modules', config_key, sender.state):
                rumps.notification("Clipboard Monitor", "Mermaid Setting",
                                  f"{sender.title} is now {'enabled' if sender.state else 'disabled'}")
                self.restart_service(None)
            else:
                rumps.notification("Error", "Failed to update Mermaid setting", "Could not save configuration")

    def set_mermaid_editor_theme(self, sender):
        """Set Mermaid editor theme."""
        print(f"DEBUG: Setting theme to {sender.title}")

        # Update all theme menu item states using stored references
        for item_name, item in self.mermaid_theme_items.items():
            old_state = item.state
            item.state = (item_name == sender.title)
            print(f"DEBUG: Menu item '{item_name}' state: {old_state} -> {item.state}")

        theme_map = {"Default": "default", "Dark": "dark", "Forest": "forest", "Neutral": "neutral"}
        new_theme = theme_map[sender.title]
        print(f"DEBUG: Mapped theme: {new_theme}")

        if self.set_config_and_reload('modules', 'mermaid_editor_theme', new_theme):
            print(f"DEBUG: Successfully saved theme {new_theme}")
            rumps.notification("Clipboard Monitor", "Mermaid Editor Theme",
                              f"Editor theme set to {sender.title}")
            self.restart_service(None)
        else:
            print(f"DEBUG: Failed to save theme {new_theme}")
            rumps.notification("Error", "Failed to update Mermaid editor theme", "Could not save configuration")

    def _build_main_menu(self):
        """Build the clean modular menu structure - Option D: Invisible Disabled."""
        # Section 1: Status & Service Control
        self.menu.add(self.status_item)
        self.menu.add(self.memory_menubar_item)  # Memory visualization line 1
        self.menu.add(self.memory_service_item)  # Memory visualization line 2
        self.menu.add(rumps.separator)
        self.menu.add(self.pause_toggle)
        self.menu.add(self.service_control_menu)
        self.menu.add(rumps.separator)

        # Section 2: Enabled Modules Only (completely hide disabled modules)
        self._add_enabled_modules_to_menu()

        # Module Management (moved from Settings for easier access)
        self.menu.add(self._create_enable_disable_modules_menu())
        self.menu.add(rumps.separator)

        # Unified Memory Dashboard (moved from Memory Monitor menu)
        self.menu.add(self.memory_unified_dashboard_item)
        self.menu.add(rumps.separator)

        # Section 3: Settings (includes module discovery)
        self.menu.add(self._create_clean_settings_menu())
        self.menu.add(rumps.separator)

        # Section 4: Application (Logs then Quit)
        self.menu.add(self.logs_menu)
        self.menu.add(self.quit_item)

    def _add_enabled_modules_to_menu(self):
        """Add only enabled modules to the main menu with their functionality grouped."""
        # Check if history module is enabled and add clipboard history functionality
        if self._is_module_enabled("history_module"):
            self._add_clipboard_history_menu()

        # Add other enabled modules
        enabled_modules = self._get_enabled_modules()
        for module_name in enabled_modules:
            if module_name != "history_module":  # History handled separately above
                self._add_module_menu(module_name)

        # Add separator if any modules were added
        if enabled_modules:
            self.menu.add(rumps.separator)

    def _is_module_enabled(self, module_name):
        """Check if a module is enabled."""
        config_value = self.module_status.get(module_name, True)
        return config_value not in [0, False]

    def _get_enabled_modules(self):
        """Get list of enabled module names."""
        enabled = []
        modules_dir = os.path.join(os.path.dirname(__file__), 'modules')
        if os.path.exists(modules_dir):
            for filename in os.listdir(modules_dir):
                if filename.endswith('_module.py'):
                    module_name = filename[:-3]
                    if self._is_module_enabled(module_name):
                        enabled.append(module_name)
        return enabled

    def _add_clipboard_history_menu(self):
        """Add clipboard history functionality as a grouped module."""
        clipboard_menu = rumps.MenuItem("📚 Clipboard History")
        clipboard_menu.add(self.recent_history_menu)
        clipboard_menu.add(rumps.MenuItem("🌐 View Full History (Browser)", callback=self.open_web_history_viewer))
        clipboard_menu.add(rumps.MenuItem("💻 View Full History (Terminal)", callback=self.open_cli_history_viewer))
        clipboard_menu.add(rumps.MenuItem("🗑️ Clear History", callback=self.clear_clipboard_history))
        self.menu.add(clipboard_menu)

    def _add_module_menu(self, module_name):
        """Add a module's menu with its settings."""
        display_name = self.module_display_names.get(module_name, module_name)

        if module_name == "markdown_module":
            self._add_markdown_module_menu(display_name)
        elif module_name == "mermaid_module":
            self._add_mermaid_module_menu(display_name)
        elif module_name == "drawio_module":
            self._add_drawio_module_menu(display_name)
        elif module_name == "code_formatter_module":
            self._add_code_formatter_module_menu(display_name)

    def _add_markdown_module_menu(self, display_name):
        """Add Markdown module menu."""
        markdown_menu = rumps.MenuItem(f"📝 {display_name}")
        modify_clipboard = rumps.MenuItem("Modify Clipboard Content", callback=self.toggle_markdown_setting)
        modify_clipboard.state = self.config_manager.get_config_value('modules', 'markdown_modify_clipboard', True)
        markdown_menu.add(modify_clipboard)
        self.menu.add(markdown_menu)

    def _add_mermaid_module_menu(self, display_name):
        """Add Mermaid module menu."""
        mermaid_menu = rumps.MenuItem(f"🧩 {display_name}")

        # Add settings directly to module menu (no Settings submenu)
        mermaid_settings = self._create_mermaid_settings_content()
        for item in mermaid_settings:
            mermaid_menu.add(item)

        self.menu.add(mermaid_menu)

    def _add_drawio_module_menu(self, display_name):
        """Add Draw.io module menu."""
        drawio_menu = rumps.MenuItem(f"🎨 {display_name}")

        # Add settings directly to module menu (no Settings submenu)
        drawio_settings = self._create_drawio_settings_content()
        for item in drawio_settings:
            drawio_menu.add(item)

        self.menu.add(drawio_menu)

    def _add_code_formatter_module_menu(self, display_name):
        """Add Code Formatter module menu."""
        formatter_menu = rumps.MenuItem(f"🔧 {display_name}")
        modify_clipboard = rumps.MenuItem("Modify Clipboard Content", callback=self.toggle_code_formatter_setting)
        modify_clipboard.state = self.config_manager.get_config_value('modules', 'code_formatter_modify_clipboard', False)
        formatter_menu.add(modify_clipboard)
        self.menu.add(formatter_menu)

    def _create_clean_settings_menu(self):
        """Create the clean settings menu."""
        settings_menu = rumps.MenuItem("⚙️ Settings")

        # Add module-specific settings for enabled modules only
        self._add_enabled_module_settings(settings_menu)

        # Add system settings
        settings_menu.add(self._create_general_settings_menu())
        settings_menu.add(self._create_performance_settings_menu())
        settings_menu.add(self._create_security_settings_menu())
        settings_menu.add(self._create_configuration_management_menu())

        return settings_menu

    def _create_enable_disable_modules_menu(self):
        """Create the 'Enable/Disable Modules' submenu showing all modules with their status."""
        modules_menu = rumps.MenuItem("🧩 Enable/Disable Modules")

        # Find all modules
        modules_dir = os.path.join(os.path.dirname(__file__), 'modules')
        if os.path.exists(modules_dir):
            for filename in sorted(os.listdir(modules_dir)):
                if filename.endswith('_module.py'):
                    module_name = filename[:-3]
                    display_name = self.module_display_names.get(module_name, module_name)
                    is_enabled = self._is_module_enabled(module_name)

                    # Create menu item with current status
                    if is_enabled:
                        status_icon = "✅"
                        action_text = "Click to disable"
                        callback = self.disable_module
                    else:
                        status_icon = "❌"
                        action_text = "Click to enable"
                        callback = self.enable_module

                    module_item = rumps.MenuItem(f"{status_icon} {display_name} ({action_text})", callback=callback)
                    module_item._module_name = module_name
                    modules_menu.add(module_item)

        return modules_menu

    def _add_enabled_module_settings(self, settings_menu):
        """Add settings submenus for enabled modules only."""
        enabled_modules = self._get_enabled_modules()

        if "history_module" in enabled_modules:
            settings_menu.add(self._create_history_settings_menu())

        # Add other module settings as needed
        # (Mermaid and Draw.io settings are already in their main menus)

    def load_module_config(self):
        """Load module configuration from config file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if 'modules' in config:
                        self.module_status = config['modules']
        except Exception as e:
            print(f"Error loading module config: {e}")
            # Default to empty dict, modules will be enabled by default
            self.module_status = {}
    
    def update_status_periodically(self):
        """Update the service status every 5 seconds"""
        while True:
            self.update_status()
            time.sleep(5)
    
    @memory_profile_function
    def update_status(self):
        """Check if the service is running and update the status menu item"""
        try:
            # Debug: Log function entry (but not too frequently)
            if hasattr(self, '_status_debug_counter'):
                self._status_debug_counter += 1
            else:
                self._status_debug_counter = 1

            if self._status_debug_counter % 12 == 0:  # Log every 12th call (every minute)
                log_memory(f"update_status called {self._status_debug_counter} times", "INFO")
            # Check if the process is running using launchctl
            # Try development service first, then production service
            service_names = ["com.clipboardmonitor.service.dev", "com.clipboardmonitor"]
            result = None

            for service_name in service_names:
                result = subprocess.run(
                    ["launchctl", "list", service_name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    break
            
            # Check for pause flag
            pause_flag_path = safe_expanduser("~/Library/Application Support/ClipboardMonitor/pause_flag")
            is_paused = os.path.exists(pause_flag_path)
            
            # If return code is 0, service is running
            if result.returncode == 0:
                if is_paused:
                    self.status_item.title = "Status: Paused"
                    self.pause_toggle.title = "Resume Monitoring"
                    return
                
                # Service is running and not paused
                # Check if it's using enhanced monitoring
                try:
                    from utils import get_app_paths
                    log_path = get_app_paths()["out_log"]
                    grep_result = subprocess.run(
                        ["grep", "-i", "enhanced clipboard monitoring", log_path],
                        capture_output=True,
                        text=True
                    )
                    
                    if grep_result.returncode == 0 and grep_result.stdout:
                        self.status_item.title = "Status: Running (Enhanced)"
                    else:
                        self.status_item.title = "Status: Running (Polling)"
                    
                    # Reset pause toggle text
                    self.pause_toggle.title = "Pause Monitoring"
                except Exception as log_error:
                    # If we can't read the log file, just show as running
                    self.status_item.title = "Status: Running"
                    self.pause_toggle.title = "Pause Monitoring"
            else:
                self.status_item.title = "Status: Stopped"
                # Reset pause toggle text
                self.pause_toggle.title = "Pause Monitoring"
                
                # Remove pause flag if service is stopped
                if is_paused and os.path.exists(pause_flag_path):
                    os.remove(pause_flag_path)
        except Exception as e:
            self.status_item.title = "Status: Error checking"
            # Log the error
            import traceback
            from utils import get_app_paths
            error_log_path = get_app_paths()["err_log"]
            with open(error_log_path, 'a') as f:
                f.write(f"Status check error: {str(e)}\n")
                f.write(traceback.format_exc())
    
    def start_service(self, _):
        try:
            subprocess.run(["launchctl", "load", self.plist_path])
            self.log_event("Service started via menu.", "INFO")
            show_notification("Clipboard Monitor", "Service Started", "The clipboard monitor service has been started.", self.log_path, self.error_log_path)
            self.update_status()
        except Exception as e:
            self.log_error(f"Failed to start service: {str(e)}")
            show_notification("Error", "Failed to start service", str(e), self.log_path, self.error_log_path)
    
    def stop_service(self, _):
        try:
            subprocess.run(["launchctl", "unload", self.plist_path])
            self.log_event("Service stopped via menu.", "INFO")
            show_notification("Clipboard Monitor", "Service Stopped", "The clipboard monitor service has been stopped.", self.log_path, self.error_log_path)
            self.update_status()
        except Exception as e:
            self.log_error(f"Failed to stop service: {str(e)}")
            show_notification("Error", "Failed to stop service", str(e), self.log_path, self.error_log_path)
    
    def restart_service(self, _):
        try:
            subprocess.run(["launchctl", "unload", self.plist_path])
            self.log_event("Service unloaded for restart.", "INFO")
            import time
            time.sleep(1)
            subprocess.run(["launchctl", "load", self.plist_path])
            self.log_event("Service loaded for restart.", "INFO")
            rumps.notification("Clipboard Monitor", "Service Restarted", "The clipboard monitor service has been restarted.")
            self.log_event("Service restarted via menu.", "INFO")
            self.update_status()

            # Auto-start dashboard after service restart
            self._auto_start_dashboard()
        except Exception as e:
            self.log_error(f"Failed to restart service: {str(e)}")
            show_notification("Error", "Failed to restart service", str(e), self.log_path, self.error_log_path)
    
    def view_output_log(self, _):
        import subprocess
        from utils import get_app_paths
        log_path = get_app_paths()["out_log"]
        subprocess.Popen(["open", log_path])
    
    def view_error_log(self, _):
        import subprocess
        from utils import get_app_paths
        error_log_path = get_app_paths()["err_log"]
        subprocess.Popen(["open", error_log_path])
    
    def clear_logs(self, _):
        from utils import get_app_paths
        paths = get_app_paths()
        try:
            # Truncate both log files
            with open(paths["out_log"], "w"): pass
            with open(paths["err_log"], "w"): pass
            show_notification("Logs Cleared", "All logs have been cleared.")
        except Exception as e:
            show_notification("Error", f"Failed to clear logs: {e}")
    
    def quit_app(self, _):
        rumps.quit_application()
    
    def toggle_module(self, sender):
        """Toggle a module on or off"""
        sender.state = not sender.state
        module_name = getattr(sender, '_module_name', sender.title)
        self.module_status[module_name] = sender.state

        # Save module status to config
        self.save_module_config()

        # Get friendly display name for notification
        display_name = self.module_display_names.get(module_name, sender.title)

        # Restart service to apply module changes
        self.restart_service(None)

        # Notify the user
        rumps.notification("Clipboard Monitor", "Module Settings",
                          f"Module '{display_name}' is now {'enabled' if sender.state else 'disabled'}")
        if module_name == "drawio_module":
            # Optionally, add any extra logic for drawio_module toggling here
            pass

        # Rebuild menu to reflect changes
        self._rebuild_menu()

    def enable_module(self, sender):
        """Enable a disabled module."""
        module_name = getattr(sender, '_module_name', None)
        if module_name:
            self.module_status[module_name] = True
            self.save_module_config()

            # Get friendly display name for notification
            display_name = self.module_display_names.get(module_name, module_name)

            # Restart service to apply module changes
            self.restart_service(None)

            # Notify the user
            rumps.notification("Clipboard Monitor", "Module Enabled",
                              f"Module '{display_name}' has been enabled")

            # Rebuild menu to show the newly enabled module
            self._rebuild_menu()

    def disable_module(self, sender):
        """Disable an enabled module."""
        module_name = getattr(sender, '_module_name', None)
        if module_name:
            self.module_status[module_name] = False
            self.save_module_config()

            # Get friendly display name for notification
            display_name = self.module_display_names.get(module_name, module_name)

            # Restart service to apply module changes
            self.restart_service(None)

            # Notify the user
            rumps.notification("Clipboard Monitor", "Module Disabled",
                              f"Module '{display_name}' has been disabled")

            # Rebuild menu to hide the disabled module
            self._rebuild_menu()

    def toggle_markdown_setting(self, sender):
        """Toggle markdown modify clipboard setting."""
        sender.state = not sender.state
        self.config_manager.set_config_value('modules', 'markdown_modify_clipboard', sender.state)
        self.config_manager.save_config()
        rumps.notification("Clipboard Monitor", "Markdown Settings",
                          f"Modify clipboard is now {'enabled' if sender.state else 'disabled'}")

    def toggle_code_formatter_setting(self, sender):
        """Toggle code formatter modify clipboard setting."""
        sender.state = not sender.state
        self.config_manager.set_config_value('modules', 'code_formatter_modify_clipboard', sender.state)
        self.config_manager.save_config()
        rumps.notification("Clipboard Monitor", "Code Formatter Settings",
                          f"Modify clipboard is now {'enabled' if sender.state else 'disabled'}")

    def _rebuild_menu(self):
        """Rebuild the entire menu structure."""
        # Clear the current menu
        self.menu.clear()

        # Reinitialize menu items and submenus
        self._init_menu_items()
        self._init_submenus()
        self._init_preferences_menu()

        # Rebuild the main menu
        self._build_main_menu()

        # Restart history updates if history module is enabled
        if self._is_module_enabled("history_module"):
            # Stop existing timer if running
            if hasattr(self, 'history_timer') and self.history_timer:
                self.history_timer.stop()
            # Start new timer
            self.initial_history_update(None)
    
    def toggle_debug(self, sender):
        """Toggle debug mode"""
        sender.state = not sender.state
        if set_config_value('general', 'debug_mode', sender.state):
            rumps.notification("Clipboard Monitor", "Debug Mode",
                              f"Debug mode is now {'enabled' if sender.state else 'disabled'}")
            self.restart_service(None)
        else:
            rumps.notification("Error", "Failed to update debug mode", "Could not save configuration")

    def set_notification_title(self, _):
        """Set custom notification title"""
        current_title = self.config_manager.get_config_value('general', 'notification_title', 'Clipboard Monitor')
        response = rumps.Window(
            message="Enter notification title:",
            title="Set Notification Title",
            default_text=current_title,
            ok="Set",
            cancel="Cancel",
            dimensions=(300, 20)
        ).run()

        if response.clicked and response.text.strip():
            if set_config_value('general', 'notification_title', response.text.strip()):
                rumps.notification("Clipboard Monitor", "Notification Title",
                                  f"Notification title set to: {response.text.strip()}")
                self.restart_service(None)
            else:
                rumps.notification("Error", "Failed to update notification title", "Could not save configuration")

    def set_enhanced_interval(self, sender):
        """Set the enhanced check interval"""
        print(f"DEBUG: Setting enhanced check interval to {sender.title}")

        # Update all menu item states using stored references
        for item_name, item in self.enhanced_interval_items.items():
            old_state = item.state
            item.state = (item_name == sender.title)
            print(f"DEBUG: Enhanced interval '{item_name}' state: {old_state} -> {item.state}")

        # Get the new interval value
        new_interval = self.enhanced_options[sender.title]
        print(f"DEBUG: Mapped enhanced interval: {new_interval}")

        if self.set_config_and_reload('general', 'enhanced_check_interval', new_interval):
            print(f"DEBUG: Successfully saved enhanced check interval {new_interval}")
            rumps.notification("Clipboard Monitor", "Enhanced Check Interval",
                              f"Enhanced check interval set to {new_interval} seconds")
            self.restart_service(None)
        else:
            print(f"DEBUG: Failed to save enhanced check interval {new_interval}")
            rumps.notification("Error", "Failed to update enhanced check interval", "Could not save configuration")

    def toggle_performance_setting(self, sender):
        """Toggle performance settings"""
        sender.state = not sender.state

        # Map menu item titles to config keys
        setting_map = {
            "Lazy Module Loading": "lazy_module_loading",
            "Adaptive Checking": "adaptive_checking",
            "Process Large Content": "process_large_content"
            # Memory-related settings moved to toggle_memory_setting
        }

        config_key = setting_map.get(sender.title)
        if config_key and set_config_value('performance', config_key, sender.state):
            rumps.notification("Clipboard Monitor", "Performance Setting",
                              f"{sender.title} is now {'enabled' if sender.state else 'disabled'}")
            self.restart_service(None)
        else:
            rumps.notification("Error", "Failed to update performance setting", "Could not save configuration")

    def toggle_memory_setting(self, sender):
        """Toggle memory-specific settings."""
        sender.state = not sender.state

        setting_map = {
            "Memory Optimization": ("performance", "memory_optimization"),
            "Memory Logging": ("performance", "memory_logging"),
            "Auto Memory Cleanup": ("memory", "auto_cleanup"),
            "Memory Leak Detection": ("memory", "leak_detection")
        }

        config_section, config_key = setting_map.get(sender.title, (None, None))
        if config_section and config_key:
            if set_config_value(config_section, config_key, sender.state):
                rumps.notification("Clipboard Monitor", "Memory Setting",
                                  f"{sender.title} is now {'enabled' if sender.state else 'disabled'}")
                self.restart_service(None)
            else:
                rumps.notification("Error", "Failed to update memory setting", "Could not save configuration")

    def set_max_execution_time(self, _):
        """Set maximum module execution time"""
        current_time = self.config_manager.get_config_value('performance', 'max_module_execution_time', 500)
        response = rumps.Window(
            message="Enter maximum execution time (milliseconds):",
            title="Set Max Execution Time",
            default_text=str(current_time),
            ok="Set",
            cancel="Cancel",
            dimensions=(300, 20)
        ).run()

        if response.clicked and response.text.strip():
            try:
                new_time = int(response.text.strip())
                if new_time > 0:
                    if set_config_value('performance', 'max_module_execution_time', new_time):
                        rumps.notification("Clipboard Monitor", "Max Execution Time",
                                          f"Max execution time set to {new_time}ms")
                        self.restart_service(None)
                    else:
                        rumps.notification("Error", "Failed to update execution time", "Could not save configuration")
                else:
                    rumps.notification("Error", "Invalid Value", "Execution time must be positive")
            except ValueError:
                rumps.notification("Error", "Invalid Value", "Please enter a valid number")
    
    def set_polling_interval(self, sender):
        """Set the polling interval"""
        print(f"DEBUG: Setting polling interval to {sender.title}")

        # Update all menu item states using stored references
        for item_name, item in self.polling_interval_items.items():
            old_state = item.state
            item.state = (item_name == sender.title)
            print(f"DEBUG: Polling interval '{item_name}' state: {old_state} -> {item.state}")

        # Get the new interval value
        new_interval = self.polling_options[sender.title]
        print(f"DEBUG: Mapped polling interval: {new_interval}")

        if self.set_config_and_reload('general', 'polling_interval', new_interval):
            print(f"DEBUG: Successfully saved polling interval {new_interval}")
            rumps.notification("Clipboard Monitor", "Polling Interval",
                              f"Polling interval set to {new_interval} seconds")
            self.restart_service(None)
        else:
            print(f"DEBUG: Failed to save polling interval {new_interval}")
            rumps.notification("Error", "Failed to update polling interval", "Could not save configuration")

    def set_max_history_items(self, _):
        """Set maximum history items for both menu and storage"""
        current_max = self.config_manager.get_config_value('history', 'max_items', 20)
        response = rumps.Window(
            message="Enter maximum number of recent items to show in menu:",
            title="Set Max Recent Menu Items",
            default_text=str(current_max),
            ok="Set",
            cancel="Cancel",
            dimensions=(300, 20)
        ).run()

        if response.clicked and response.text.strip():
            try:
                new_max = int(response.text.strip())
                if new_max > 0:
                    if set_config_value('history', 'max_items', new_max):
                        self.log_event(f"Set max_items to {new_max}", "INFO")
                        rumps.notification("Clipboard Monitor", "Max Recent Menu Items",
                                          f"Max recent menu items set to {new_max}")
                        self.update_recent_history_menu()
                    else:
                        self.log_error("Failed to update max menu items in config.")
                        rumps.notification("Error", "Failed to update max menu items", "Could not save configuration")
                else:
                    self.log_error("Attempted to set max_items to non-positive value.")
                    rumps.notification("Error", "Invalid Value", "Max items must be positive")
                    self.update_recent_history_menu()
            except ValueError:
                self.log_error("Invalid value entered for max_items.")
                rumps.notification("Error", "Invalid Value", "Please enter a valid number")

    def set_max_content_length(self, _):
        """Set maximum content length for history"""
        current_length = self.config_manager.get_config_value('history', 'max_content_length', 10000)
        response = rumps.Window(
            message="Enter maximum content length (characters):",
            title="Set Max Content Length",
            default_text=str(current_length),
            ok="Set",
            cancel="Cancel",
            dimensions=(300, 20)
        ).run()

        if response.clicked and response.text.strip():
            try:
                new_length = int(response.text.strip())
                if new_length > 0:
                    if set_config_value('history', 'max_content_length', new_length):
                        rumps.notification("Clipboard Monitor", "Max Content Length",
                                          f"Max content length set to {new_length} characters")
                        self.restart_service(None)
                    else:
                        rumps.notification("Error", "Failed to update max content length", "Could not save configuration")
                else:
                    rumps.notification("Error", "Invalid Value", "Content length must be positive")
            except ValueError:
                rumps.notification("Error", "Invalid Value", "Please enter a valid number")

    def set_history_location(self, _):
        """Set history file location"""
        current_location = self.config_manager.get_config_value('history', 'save_location',
        "~/Library/Application Support/ClipboardMonitor/clipboard_history.json")
        response = rumps.Window(
            message="Enter history file location:",
            title="Set History Location",
            default_text=current_location,
            ok="Set",
            cancel="Cancel",
            dimensions=(400, 20)
        ).run()

        if response.clicked and response.text.strip():
            if set_config_value('history', 'save_location', response.text.strip()):
                rumps.notification("Clipboard Monitor", "History Location",
                                  f"History location set to: {response.text.strip()}")
                self.restart_service(None)
            else:
                rumps.notification("Error", "Failed to update history location", "Could not save configuration")

    def toggle_security_setting(self, sender):
        """Toggle security settings"""
        sender.state = not sender.state

        # Map menu item titles to config keys
        setting_map = {
            "Sanitize Clipboard": "sanitize_clipboard"
        }

        config_key = setting_map.get(sender.title)
        if config_key and set_config_value('security', config_key, sender.state):
            rumps.notification("Clipboard Monitor", "Security Setting",
                              f"{sender.title} is now {'enabled' if sender.state else 'disabled'}")
            self.restart_service(None)
        else:
            rumps.notification("Error", "Failed to update security setting", "Could not save configuration")

    def set_max_clipboard_size(self, _):
        """Set maximum clipboard size"""
        current_size = self.config_manager.get_config_value('security', 'max_clipboard_size', 10485760)
        # Convert to MB for user-friendly display
        current_mb = current_size / (1024 * 1024)
        response = rumps.Window(
            message="Enter maximum clipboard size (MB):",
            title="Set Max Clipboard Size",
            default_text=str(int(current_mb)),
            ok="Set",
            cancel="Cancel",
            dimensions=(300, 20)
        ).run()

        if response.clicked and response.text.strip():
            try:
                new_mb = float(response.text.strip())
                if new_mb > 0:
                    new_bytes = int(new_mb * 1024 * 1024)
                    if set_config_value('security', 'max_clipboard_size', new_bytes):
                        rumps.notification("Clipboard Monitor", "Max Clipboard Size",
                                          f"Max clipboard size set to {new_mb} MB")
                        self.restart_service(None)
                    else:
                        rumps.notification("Error", "Failed to update max clipboard size", "Could not save configuration")
                else:
                    rumps.notification("Error", "Invalid Value", "Size must be positive")
            except ValueError:
                rumps.notification("Error", "Invalid Value", "Please enter a valid number")

    def reset_config_to_defaults(self, _):
        """Reset configuration to default values"""
        response = rumps.alert(
            title="Reset Configuration",
            message="Are you sure you want to reset all settings to defaults? This cannot be undone.",
            ok="Reset",
            cancel="Cancel"
        )

        if response == 1:  # OK clicked
            default_config = {
                "general": {
                    "debug_mode": False,
                    "notification_title": "Clipboard Monitor",
                    "polling_interval": 1.0,
                    "enhanced_check_interval": 0.1
                },
                "performance": {
                    "lazy_module_loading": True,
                    "adaptive_checking": True,
                    "memory_optimization": True,
                    "process_large_content": True,
                    "max_module_execution_time": 500
                },
                "history": {
                    "max_items": 100,
                    "max_content_length": 10000,
                    "save_location": "~/Library/Application Support/ClipboardMonitor/clipboard_history.json"
                },
                "security": {
                    "sanitize_clipboard": True,
                    "max_clipboard_size": 10485760
                }
            }

            try:
                config_path = os.path.join(os.path.dirname(__file__), 'config.json')
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)

                rumps.notification("Clipboard Monitor", "Configuration Reset",
                                  "Configuration has been reset to defaults")
                self.restart_service(None)
            except Exception as e:
                rumps.notification("Error", "Failed to reset configuration", str(e))

    def export_configuration(self, _):
        """Export current configuration to a file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            if os.path.exists(config_path):
                # Get export location from user
                response = rumps.Window(
                    message="Enter export file path:",
                    title="Export Configuration",
                    default_text="~/Desktop/clipboard_monitor_config.json",
                    ok="Export",
                    cancel="Cancel",
                    dimensions=(400, 20)
                ).run()

                if response.clicked and response.text.strip():
                    export_path = safe_expanduser(response.text.strip())

                    # Copy config file
                    import shutil
                    shutil.copy2(config_path, export_path)

                    rumps.notification("Clipboard Monitor", "Configuration Exported",
                                      f"Configuration exported to: {export_path}")
                else:
                    rumps.notification("Error", "Export cancelled", "No file path provided")
            else:
                rumps.notification("Error", "No configuration found", "Config file does not exist")
        except Exception as e:
            rumps.notification("Error", "Failed to export configuration", str(e))

    def import_configuration(self, _):
        """Import configuration from a file"""
        response = rumps.Window(
            message="Enter configuration file path:",
            title="Import Configuration",
            default_text="~/Desktop/clipboard_monitor_config.json",
            ok="Import",
            cancel="Cancel",
            dimensions=(400, 20)
        ).run()

        if response.clicked and response.text.strip():
            import_path = safe_expanduser(response.text.strip())

            try:
                if os.path.exists(import_path):
                    # Validate the imported config
                    with open(import_path, 'r') as f:
                        imported_config = json.load(f)

                    # Copy to current config location
                    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
                    import shutil
                    shutil.copy2(import_path, config_path)

                    rumps.notification("Clipboard Monitor", "Configuration Imported",
                                      f"Configuration imported from: {import_path}")
                    self.restart_service(None)
                else:
                    rumps.notification("Error", "File not found", f"Could not find: {import_path}")
            except json.JSONDecodeError:
                rumps.notification("Error", "Invalid configuration file", "File is not valid JSON")
            except Exception as e:
                rumps.notification("Error", "Failed to import configuration", str(e))

    def view_current_configuration(self, _):
        """Display current configuration in a dialog"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)

                # Format config for display
                config_text = json.dumps(config, indent=2)

                # Show in a dialog (truncate if too long)
                if len(config_text) > 1000:
                    config_text = config_text[:1000] + "\n... (truncated)"

                rumps.alert(
                    title="Current Configuration",
                    message=config_text,
                    ok="OK"
                )
            else:
                rumps.notification("Error", "No configuration found", "Config file does not exist")
        except Exception as e:
            rumps.notification("Error", "Failed to view configuration", str(e))

    def toggle_clipboard_modification(self, sender):
        """Toggle clipboard modification settings for modules"""
        sender.state = not sender.state

        # Map menu item titles to config keys
        setting_map = {
            "Markdown Modify Clipboard": "markdown_modify_clipboard",
            "Code Formatter Modify Clipboard": "code_formatter_modify_clipboard"
        }

        config_key = setting_map.get(sender.title)
        if config_key and set_config_value('modules', config_key, sender.state):
            status = "enabled" if sender.state else "disabled"
            rumps.notification("Clipboard Monitor", "Clipboard Modification",
                              f"{sender.title} is now {status}")
            self.restart_service(None)
        else:
            rumps.notification("Error", "Failed to update clipboard modification setting", "Could not save configuration")

    def save_module_config(self):
        """Save module configuration to config file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            
            # Load existing config if it exists
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Update modules section
            config['modules'] = self.module_status
            
            # Write back to file
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            rumps.notification("Error", "Failed to save module config", str(e))
    
    def open_web_history_viewer(self, _):
        """Open the web-based clipboard history viewer"""
        try:
            web_viewer = os.path.join(os.path.dirname(__file__), 'web_history_viewer.py')
            if os.path.exists(web_viewer):
                # Launch the web-based history viewer
                process = subprocess.Popen(
                    ["/usr/bin/python3", web_viewer],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                # Check if process started successfully
                try:
                    # Wait a short time to see if it fails immediately
                    process.wait(timeout=2.0)
                    if process.returncode == 0:
                        rumps.notification("Success", "History Viewer", "Clipboard history opened in browser")
                    else:
                        stderr_output = process.stderr.read().decode('utf-8')
                        rumps.notification("Error", "History Viewer Failed",
                                          f"Exit code: {process.returncode}\n{stderr_output}")
                except subprocess.TimeoutExpired:
                    # Process is still running, which might be normal
                    rumps.notification("Success", "History Viewer", "Clipboard history opened in browser")
            else:
                rumps.notification("Error", "History Viewer Not Found",
                                  "Could not find web_history_viewer.py")
        except Exception as e:
            rumps.notification("Error", "Failed to open history viewer", str(e))

    def open_cli_history_viewer(self, _):
        """Open the command-line clipboard history viewer"""
        try:
            cli_viewer = os.path.join(os.path.dirname(__file__), 'cli_history_viewer.py')
            if os.path.exists(cli_viewer):
                # Use a simpler approach - open Terminal with the command
                script_dir = os.path.dirname(cli_viewer)

                # Create a temporary script to run
                temp_script = f'''#!/bin/bash
cd "{script_dir}"
echo "📋 Clipboard History Viewer"
echo "=========================="
python3 cli_history_viewer.py
echo ""
echo "Press any key to close this window..."
read -n 1
'''

                # Write temp script
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
                    f.write(temp_script)
                    temp_script_path = f.name

                # Make it executable
                os.chmod(temp_script_path, 0o755)

                # Open Terminal with the script
                subprocess.run(['open', '-a', 'Terminal', temp_script_path])

                rumps.notification("Success", "History Viewer", "Clipboard history opened in Terminal")
            else:
                rumps.notification("Error", "History Viewer Not Found",
                                  "Could not find cli_history_viewer.py")
        except Exception as e:
            rumps.notification("Error", "Failed to open CLI history viewer", str(e))

    # Removed initial_history_update - now handled inline during initialization

    @memory_profile_function
    def periodic_history_update(self, _):
        """Periodic history menu update - called every 30 seconds on main thread"""
        # Debug: Log periodic history updates
        if hasattr(self, '_history_debug_counter'):
            self._history_debug_counter += 1
        else:
            self._history_debug_counter = 1

        if self._history_debug_counter % 10 == 0:  # Log every 10th call (every 5 minutes)
            log_memory(f"periodic_history_update called {self._history_debug_counter} times", "INFO")

        self.update_recent_history_menu()

    @memory_profile_function
    def update_recent_history_menu(self):
        """Update the recent history menu, limiting items and clearing references."""
        import gc
        import traceback        
        # Read max_items from config file (history section), default to 20 if not set
        max_items = self.config_manager.get_config_value('history', 'max_items', 20)
        debug_mode = self.config_manager.get_config_value('general', 'debug_mode', False)
        try:
            max_items = int(max_items)
        except (ValueError, TypeError):
            max_items = 20
        try:
            # Clear the existing menu items instead of recreating the menu
            self.recent_history_menu.clear()

            history = load_clipboard_history() or []
            num_loaded = len(history)
            num_displayed = 0
            if not history:
                placeholder = rumps.MenuItem("(No clipboard history found)")
                placeholder.set_callback(None)
                self.recent_history_menu.add(placeholder)
            else:
                for i, item in enumerate(history[:max_items]):
                    # Extract clipboard text from history dicts
                    if isinstance(item, dict):
                        display_text = item.get("content", "")
                    else:
                        display_text = str(item)
                    menu_item = rumps.MenuItem(
                        f"{display_text[:50]}..." if len(display_text) > 50 else display_text,
                        callback=self.copy_history_item
                    )
                    menu_item._history_identifier = item.get("hash", "") # Store a small identifier, not full content
                    self.recent_history_menu.add(menu_item)
                    num_displayed += 1

            # Add a separator and clear history option
            self.recent_history_menu.add(rumps.separator)
            clear_history_item = rumps.MenuItem("🗑️ Clear History")
            clear_history_item.set_callback(self.clear_clipboard_history)
            self.recent_history_menu.add(clear_history_item)

            gc.collect()  # Explicitly collect garbage after menu update
            # Debug notifications/logs
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Remove any ANSI color codes from log messages
            import re
            # msg = f"[{timestamp}] update_recent_history_menu: loaded={num_loaded}, displayed={num_displayed}"
            # ansi_escape = re.compile(r'\x1B\[[0-9;]*[mK]')
            # msg = ansi_escape.sub('', msg)
            if debug_mode:
                rumps.notification("Clipboard Monitor Debug", "Recent History Menu", f"Recent history menu updated: loaded={num_loaded}, displayed={num_displayed}")
                # Logging of update_recent_history_menu is intentionally suppressed per user request
        except Exception as e:
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Remove any ANSI color codes from error messages
            import re
            err_msg = f"[{timestamp}] Exception in update_recent_history_menu: {str(e)}\n{traceback.format_exc()}"
            ansi_escape = re.compile(r'\x1B\[[0-9;]*[mK]')
            err_msg = ansi_escape.sub('', err_msg)
            rumps.notification("Clipboard Monitor Error", "Menu Update Failed", str(e))
            with open(self.error_log_path, 'a') as f:
                f.write(err_msg + "\n")
            # Clear and add a placeholder if menu fails
            self.recent_history_menu.clear()
            placeholder = rumps.MenuItem("(Error loading clipboard history)")
            placeholder.set_callback(None)
            self.recent_history_menu.add(placeholder)
            gc.collect()

    def copy_history_item(self, sender):
        """Copy a history item to clipboard by identifier"""
        try:
            history_identifier = getattr(sender, '_history_identifier', None)
            if history_identifier:
                # Reload history to get the full content of the specific item
                # This is done to avoid storing large content strings directly on menu items
                # which can lead to memory leaks if rumps doesn't properly release them.
                # Note: This reloads the entire history file, which can be inefficient for very large files.
                print(f"DEBUG: Reloading history to copy item with identifier: {history_identifier}")
                full_history = load_clipboard_history()
                content_to_copy = None
                for item in full_history:
                    if item.get("hash") == history_identifier:
                        content_to_copy = item.get("content", "")
                        break
                
                if content_to_copy:
                    if PYPERCLIP_AVAILABLE:
                        pyperclip.copy(content_to_copy)
                        truncated = content_to_copy[:50] + '...' if len(content_to_copy) > 50 else content_to_copy # Use centralized notification
                        show_notification("Clipboard", "Item Copied", f"Copied: {truncated}", self.log_path, self.error_log_path)
                    else:
                        show_notification("Error", "Copy Failed", "pyperclip not available in this environment", self.log_path, self.error_log_path)
                else:
                    show_notification("Error", "Copy Failed", "Content not found in history", self.log_path, self.error_log_path)
        except Exception as e:
            show_notification("Error", "Copy Failed", str(e), self.log_path, self.error_log_path)

    def refresh_history_menu(self, _):
        """Refresh the history menu - called from menu click (already on main thread)"""
        self.update_recent_history_menu()
        rumps.notification("Clipboard Monitor", "History Refreshed", "Recent items menu updated")

    def clear_clipboard_history(self, _):
        """Clear all clipboard history with confirmation"""
        try:
            # Show confirmation dialog
            response = rumps.alert(
                title="Clear Clipboard History",
                message="Are you sure you want to clear all clipboard history? This action cannot be undone.",
                ok="Clear History",
                cancel="Cancel"
            )

            if response == 1:  # OK clicked
                try:
                    from modules.history_module import clear_history as module_clear_history
                    result = module_clear_history()
                    if result:
                        # Update the recent history menu to reflect the cleared state
                        self.update_recent_history_menu()
                        # Show success notification
                        rumps.notification("Clipboard Monitor", "History Cleared", "All clipboard history has been cleared.")
                    else:
                        rumps.notification("Error", "Failed to clear history", "Could not clear history file.")
                except Exception as file_error:
                    rumps.notification("Error", "Failed to clear history", f"Could not clear history file: {str(file_error)}")

        except Exception as e:
            rumps.notification("Error", "Exception in clear_clipboard_history", str(e))

    def toggle_monitoring(self, sender):
        """Temporarily pause or resume clipboard monitoring without stopping the service"""
        try:
            # Check if config file exists
            config_path = safe_expanduser("~/Library/Application Support/ClipboardMonitor/config.json")
            ensure_directory_exists(os.path.dirname(config_path))

            # Create pause flag file to communicate with the main process
            pause_flag_path = safe_expanduser("~/Library/Application Support/ClipboardMonitor/pause_flag")
            
            if sender.title == "Pause Monitoring":
                # Create pause flag file
                with open(pause_flag_path, 'w') as f:
                    f.write("paused")

                sender.title = "Resume Monitoring"
                self.status_item.title = "Status: Paused"

                # Show notification using direct AppleScript
                self.show_mac_notification(
                    "Clipboard Monitor",
                    "Monitoring Paused",
                    "Clipboard monitoring has been temporarily paused."
                )

                # Also try the rumps notification as backup
                rumps.notification(
                    "Clipboard Monitor",
                    "Monitoring Paused",
                    "Clipboard monitoring has been temporarily paused."
                )
            else:
                # Remove pause flag file
                if os.path.exists(pause_flag_path):
                    os.remove(pause_flag_path)

                sender.title = "Pause Monitoring"
                self.status_item.title = "Status: Running"

                # Show notification using direct AppleScript
                self.show_mac_notification(
                    "Clipboard Monitor",
                    "Monitoring Resumed",
                    "Clipboard monitoring has been resumed."
                )

                # Also try the rumps notification as backup
                rumps.notification(
                    "Clipboard Monitor",
                    "Monitoring Resumed",
                    "Clipboard monitoring has been resumed."
                )

                # Update status after a short delay to get accurate status
                threading.Timer(1.0, self.update_status).start()
        
        except Exception as e:
            # Try to show error notification
            try:
                self.show_mac_notification("Error", "Failed to toggle monitoring", str(e))
            except:
                pass
            
            # Log the full error for debugging
            import traceback
            with open(self.error_log_path, 'a') as f:
                f.write(f"Toggle monitoring error: {str(e)}\n")
                f.write(traceback.format_exc())

    def start_memory_visualizer(self, sender):
        """Start the Memory Visualizer dashboard"""
        try:
            import subprocess
            import webbrowser

            # Check if already running using system-wide process detection
            if self._is_process_running('visualizer'):
                webbrowser.open('http://localhost:8001')
                rumps.notification("Memory Visualizer", "Already Running", "Opening existing dashboard...")
                return

            # Start the memory visualizer as a separate process
            script_path = os.path.join(os.path.dirname(__file__), 'memory_visualizer.py')

            if os.path.exists(script_path):
                proc = subprocess.Popen([sys.executable, script_path],
                                      cwd=os.path.dirname(__file__))
                self._monitoring_processes['visualizer'] = proc

                # Give it a moment to start
                import time
                time.sleep(2)

                # Open the browser
                webbrowser.open('http://localhost:8001')

                rumps.notification("Memory Visualizer",
                                 "Started Successfully",
                                 "Dashboard available at localhost:8001")
            else:
                rumps.alert("Memory Visualizer not found",
                          "The memory_visualizer.py file was not found.")

        except Exception as e:
            rumps.alert("Error", f"Failed to start Memory Visualizer: {e}")

    def start_monitoring_dashboard(self, sender):
        """Start the Comprehensive Monitoring Dashboard"""
        try:
            import subprocess
            import webbrowser

            # Check if already running using system-wide process detection
            if self._is_process_running('dashboard'):
                webbrowser.open('http://localhost:8002')
                rumps.notification("Monitoring Dashboard", "Already Running", "Opening existing dashboard...")
                return

            # Start the monitoring dashboard as a separate process
            script_path = os.path.join(os.path.dirname(__file__), 'memory_monitoring_dashboard.py')

            if os.path.exists(script_path):
                proc = subprocess.Popen([sys.executable, script_path],
                                      cwd=os.path.dirname(__file__))
                self._monitoring_processes['dashboard'] = proc

                # Give it a moment to start
                import time
                time.sleep(2)

                # Open the browser
                webbrowser.open('http://localhost:8002')

                rumps.notification("Monitoring Dashboard",
                                 "Started Successfully",
                                 "Dashboard available at localhost:8002")
            else:
                rumps.alert("Monitoring Dashboard not found",
                          "The memory_monitoring_dashboard.py file was not found.")

        except Exception as e:
            rumps.alert("Error", f"Failed to start Monitoring Dashboard: {e}")

    def start_unified_dashboard(self, sender):
        """Start the Unified Memory Dashboard (combines visualizer and monitoring)."""
        try:
            import subprocess
            import webbrowser
            import time

            # Kill any existing dashboard processes first
            dashboard_processes = ['unified_dashboard', 'visualizer', 'monitoring_dashboard']
            for process_name in dashboard_processes:
                if self._is_process_running(process_name):
                    self._kill_monitoring_process(process_name)

            # Start unified dashboard
            script_path = os.path.join(os.path.dirname(__file__), 'unified_memory_dashboard.py')

            # For bundled app, try alternative paths
            if not os.path.exists(script_path):
                # Try in the Resources directory for bundled app
                script_path = os.path.join(os.path.dirname(__file__), '..', 'Resources', 'unified_memory_dashboard.py')

            if not os.path.exists(script_path):
                # Try in the Frameworks directory for bundled app
                script_path = os.path.join(os.path.dirname(__file__), '..', 'Frameworks', 'unified_memory_dashboard.py')

            if os.path.exists(script_path):
                print(f"Starting unified dashboard from: {script_path}")

                # Test if the script can be imported (basic syntax check)
                try:
                    import subprocess

                    # Use the same Python executable logic as the main launch
                    test_python = sys.executable
                    if getattr(sys, 'frozen', False):
                        # Find Python with psutil for testing
                        python_candidates = ['/usr/bin/python3', '/usr/local/bin/python3', '/opt/homebrew/bin/python3']
                        test_python = '/usr/bin/python3'  # fallback
                        for candidate in python_candidates:
                            if os.path.exists(candidate):
                                try:
                                    test_proc = subprocess.run([candidate, '-c', 'import psutil'],
                                                             capture_output=True, timeout=3)
                                    if test_proc.returncode == 0:
                                        test_python = candidate
                                        break
                                except:
                                    continue

                    test_proc = subprocess.run([test_python, '-c', f'import sys; sys.path.insert(0, "{os.path.dirname(script_path)}"); import unified_memory_dashboard'],
                                             capture_output=True, timeout=10)
                    if test_proc.returncode != 0:
                        rumps.alert("Dashboard Import Error",
                                   f"The dashboard script has syntax errors:\n\n{test_proc.stderr.decode()}")
                        return
                except Exception as e:
                    print(f"Warning: Could not test dashboard import: {e}")

                # Kill any existing dashboard processes first (more thorough cleanup)
                try:
                    import psutil
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            cmdline = proc.info.get('cmdline', [])
                            if cmdline:
                                cmdline_str = ' '.join(cmdline)
                                if 'unified_memory_dashboard.py' in cmdline_str:
                                    print(f"Killing existing dashboard process: {proc.info['pid']}")
                                    proc.terminate()
                        except:
                            continue
                    time.sleep(1)  # Give processes time to terminate
                except:
                    pass

                # Determine the correct Python executable for PyInstaller
                python_executable = sys.executable

                # For PyInstaller bundles, we need to use a Python with psutil installed
                if getattr(sys, 'frozen', False):
                    # Try to find a Python with psutil installed
                    python_candidates = [
                        '/usr/bin/python3',
                        '/usr/local/bin/python3',
                        '/opt/homebrew/bin/python3',
                        sys.executable
                    ]

                    python_executable = None
                    for candidate in python_candidates:
                        if os.path.exists(candidate):
                            try:
                                # Test if this Python has psutil
                                test_proc = subprocess.run([candidate, '-c', 'import psutil; print("OK")'],
                                                         capture_output=True, timeout=5)
                                if test_proc.returncode == 0 and b'OK' in test_proc.stdout:
                                    python_executable = candidate
                                    print(f"Found Python with psutil: {candidate}")
                                    break
                            except:
                                continue

                    # Fallback to system Python if none found
                    if not python_executable:
                        python_executable = '/usr/bin/python3'
                        print("Warning: No Python with psutil found, using system Python")

                print(f"Using Python executable: {python_executable}")

                # Start new dashboard instance
                proc = subprocess.Popen([python_executable, script_path],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      cwd=os.path.dirname(script_path))
                self._monitoring_processes['unified_dashboard'] = proc

                # Wait for server to start and check if it's actually running
                print("Waiting for dashboard server to start...")
                for i in range(10):  # Wait up to 10 seconds
                    time.sleep(1)
                    try:
                        import urllib.request
                        urllib.request.urlopen('http://localhost:8001', timeout=1)
                        print("Dashboard server is responding")
                        break
                    except:
                        if i == 9:  # Last attempt
                            print("Dashboard server failed to start")
                            # Check if process is still running
                            if proc.poll() is not None:
                                stdout, stderr = proc.communicate()
                                print(f"Dashboard process exited with code: {proc.returncode}")
                                print(f"Stdout: {stdout.decode()}")
                                print(f"Stderr: {stderr.decode()}")

                                # Show detailed error information
                                error_msg = f"Dashboard failed to start.\n\nExit code: {proc.returncode}"
                                if stderr:
                                    error_msg += f"\n\nError details:\n{stderr.decode()}"
                                if stdout:
                                    error_msg += f"\n\nOutput:\n{stdout.decode()}"

                                rumps.alert("Dashboard Error", error_msg)
                                return
                        continue

                # Browser will be opened automatically by the dashboard
                rumps.notification("Unified Memory Dashboard", "Started Successfully",
                                 "Comprehensive monitoring available at localhost:8001")
            else:
                rumps.alert("Unified Dashboard not found",
                           f"The unified_memory_dashboard.py file was not found.\nSearched paths:\n{script_path}")

        except Exception as e:
            rumps.alert("Error", f"Failed to start Unified Memory Dashboard: {e}")

    def _auto_start_dashboard(self):
        """Auto-start unified dashboard on app launch (silent, no browser opening)"""
        debug_log_path = safe_expanduser("~/Library/Logs/ClipboardMonitor_dashboard_debug.log")

        try:
            import subprocess
            import time
            import os
            import datetime

            # Enhanced debug logging
            with open(debug_log_path, 'a') as f:
                f.write(f"[{datetime.datetime.now()}] _auto_start_dashboard called\n")
                f.write(f"  Current working directory: {os.getcwd()}\n")
                f.write(f"  __file__: {__file__}\n")
                f.write(f"  sys.argv: {sys.argv}\n")
                f.write(f"  sys.executable: {sys.executable}\n")
                f.write(f"  sys.frozen: {getattr(sys, 'frozen', False)}\n")

            # Write debug to file since print doesn't work in PyInstaller
            with open('/tmp/clipboard_debug.log', 'a') as f:
                f.write(f"DEBUG: _auto_start_dashboard called at {time.time()}\n")
            print("DEBUG: _auto_start_dashboard called")

            # PROTECTION: Check if we're already being launched by a dashboard process
            # This prevents recursive spawning
            current_cmdline = ' '.join(sys.argv)
            if '--auto-start' in current_cmdline or 'unified_memory_dashboard.py' in current_cmdline:
                with open(debug_log_path, 'a') as f:
                    f.write("  Detected dashboard launch context, skipping auto-start to prevent recursion\n")
                print("Detected dashboard launch context, skipping auto-start to prevent recursion")
                return

            # PROTECTION: Check for multiple ClipboardMonitor processes
            try:
                import psutil
                clipboard_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline:
                            cmdline_str = ' '.join(cmdline).lower()
                            if 'clipboardmonitorMenuBar' in cmdline_str or 'menu_bar_app.py' in cmdline_str:
                                clipboard_processes.append(proc.info['pid'])
                    except:
                        continue

                if len(clipboard_processes) > 1:
                    print(f"Multiple ClipboardMonitor processes detected ({len(clipboard_processes)}), skipping auto-start")
                    return
            except:
                pass  # If psutil check fails, continue with caution

            # Check if already running
            if self._is_process_running('unified_dashboard'):
                print("Unified dashboard already running, skipping auto-start")
                return

            with open('/tmp/clipboard_debug.log', 'a') as f:
                f.write(f"DEBUG: No existing dashboard found, proceeding with auto-start at {time.time()}\n")
            print("DEBUG: No existing dashboard found, proceeding with auto-start")

            # Kill any existing dashboard processes first
            dashboard_processes = ['unified_dashboard', 'visualizer', 'monitoring_dashboard']
            for process_name in dashboard_processes:
                if self._is_process_running(process_name):
                    self._kill_monitoring_process(process_name)

            # Start unified dashboard (silent mode)
            script_path = os.path.join(os.path.dirname(__file__), 'unified_memory_dashboard.py')

            # Enhanced path detection for DMG environment
            possible_paths = [
                script_path,
                os.path.join(os.path.dirname(__file__), '..', 'Resources', 'unified_memory_dashboard.py'),
                os.path.join(os.path.dirname(__file__), '..', 'Frameworks', 'unified_memory_dashboard.py'),
                # Additional paths for DMG environment
                os.path.join(os.path.dirname(__file__), 'unified_memory_dashboard.py'),
                os.path.abspath(os.path.join(os.path.dirname(__file__), 'unified_memory_dashboard.py')),
                # Check in the same directory as the executable
                os.path.join(os.path.dirname(sys.executable), 'unified_memory_dashboard.py'),
                # Check in Resources directory relative to executable
                os.path.join(os.path.dirname(sys.executable), '..', 'Resources', 'unified_memory_dashboard.py'),
            ]

            script_found = False
            with open(debug_log_path, 'a') as f:
                f.write("  Searching for unified_memory_dashboard.py in paths:\n")
                for path in possible_paths:
                    abs_path = os.path.abspath(path)
                    exists = os.path.exists(abs_path)
                    f.write(f"    {abs_path} - {'EXISTS' if exists else 'NOT FOUND'}\n")
                    if exists and not script_found:
                        script_path = abs_path
                        script_found = True

            if script_found:
                with open(debug_log_path, 'a') as f:
                    f.write(f"  Found dashboard script at: {script_path}\n")
                print(f"DEBUG: Found dashboard script at: {script_path}")

                # PROTECTION: Add environment variable to prevent recursive launches
                env = os.environ.copy()
                env['CLIPBOARD_MONITOR_DASHBOARD_PARENT'] = str(os.getpid())

                # Use correct Python executable for PyInstaller
                python_executable = sys.executable
                if getattr(sys, 'frozen', False):
                    python_executable = '/usr/bin/python3'
                    if not os.path.exists(python_executable):
                        for alt_python in ['/usr/local/bin/python3', '/opt/homebrew/bin/python3']:
                            if os.path.exists(alt_python):
                                python_executable = alt_python
                                break

                with open(debug_log_path, 'a') as f:
                    f.write(f"  Using Python executable: {python_executable}\n")
                    f.write(f"  Starting dashboard with command: {python_executable} {script_path} --auto-start\n")

                print(f"DEBUG: Using Python executable: {python_executable}")
                print(f"DEBUG: Starting dashboard with command: {python_executable} {script_path} --auto-start")

                try:
                    proc = subprocess.Popen([python_executable, script_path, '--auto-start'],
                                          env=env,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)
                    self._monitoring_processes['unified_dashboard'] = proc

                    with open(debug_log_path, 'a') as f:
                        f.write(f"  Dashboard process started with PID: {proc.pid}\n")

                    print("Auto-started unified dashboard (5-minute timeout)")

                    # Show subtle notification
                    rumps.notification("Clipboard Monitor", "Dashboard Auto-Started",
                                     "Memory monitoring available at localhost:8001 (5min timeout)")
                except Exception as e:
                    with open(debug_log_path, 'a') as f:
                        f.write(f"  ERROR starting dashboard process: {str(e)}\n")
                    print(f"ERROR starting dashboard process: {str(e)}")
            else:
                with open(debug_log_path, 'a') as f:
                    f.write("  Unified dashboard script not found in any searched paths\n")
                print(f"DEBUG: Unified dashboard script not found at: {script_path}")
                print("Unified dashboard script not found, skipping auto-start")

        except Exception as e:
            with open(debug_log_path, 'a') as f:
                f.write(f"[{datetime.datetime.now()}] ERROR in _auto_start_dashboard: {str(e)}\n")
                import traceback
                f.write(f"  Traceback: {traceback.format_exc()}\n")
                f.write("---\n")
            print(f"Error auto-starting unified dashboard: {e}")
            # Don't show error to user for auto-start failures






    def open_memory_visualizer(self, sender):
        """Open the Memory Visualizer in a web browser"""
        try:
            import subprocess
            import webbrowser

            # Start the memory visualizer as a separate process
            script_path = os.path.join(os.path.dirname(__file__), 'memory_visualizer.py')

            if os.path.exists(script_path):
                # Start the memory visualizer server
                subprocess.Popen([sys.executable, script_path],
                               cwd=os.path.dirname(__file__))

                # Give it a moment to start
                import time
                time.sleep(2)

                # Open the browser
                webbrowser.open('http://localhost:8001')

                rumps.notification("Memory Visualizer",
                                 "Memory Visualizer started",
                                 "Opening in your browser...")
            else:
                rumps.alert("Memory Visualizer not found",
                          "The memory_visualizer.py file was not found.")

        except Exception as e:
            rumps.alert("Error", f"Failed to start Memory Visualizer: {e}")

    @memory_profile_function
    def update_memory_status(self, _):
        """Update the memory status in the menu."""
        try:
            # First try to get data from unified dashboard API if available
            try:
                import urllib.request
                import json

                with urllib.request.urlopen('http://localhost:8001/api/memory', timeout=2) as response:
                    data = json.loads(response.read().decode())

                    # Extract data from unified dashboard
                    processes = data.get('clipboard', {}).get('processes', [])
                    menubar_process = next((p for p in processes if p.get('process_type') == 'menu_bar'), None)
                    service_process = next((p for p in processes if p.get('process_type') == 'main_service'), None)

                    if menubar_process and service_process:
                        menubar_memory = menubar_process.get('memory_mb', 0)
                        service_memory = service_process.get('memory_mb', 0)

                        # Use dashboard's peak values for consistency
                        dashboard_menubar_peak = data.get('peak_menubar_memory', 0)
                        dashboard_service_peak = data.get('peak_service_memory', 0)

                        # Update our peaks to match dashboard (but don't go backwards)
                        self.menubar_peak = max(self.menubar_peak, dashboard_menubar_peak)
                        self.service_peak = max(self.service_peak, dashboard_service_peak)

                        # Update history for mini histograms
                        self.menubar_history.append(menubar_memory)
                        self.service_history.append(service_memory)

                        if len(self.menubar_history) > 10: self.menubar_history.pop(0)
                        if len(self.service_history) > 10: self.service_history.pop(0)

                        menubar_histogram = self._generate_mini_histogram(self.menubar_history, self.menubar_peak)
                        service_histogram = self._generate_mini_histogram(self.service_history, self.service_peak)

                        self.memory_menubar_item.title = f"Menu Bar: {menubar_memory:.1f}MB {menubar_histogram} Peak: {self.menubar_peak:.0f}MB"
                        self.memory_service_item.title = f"Service: {service_memory:.1f}MB  {service_histogram} Peak: {self.service_peak:.0f}MB"
                        return  # Successfully used dashboard data

            except Exception:
                # Dashboard not available, fall back to independent monitoring
                pass

            # Fallback: Independent monitoring (original code)
            import psutil
            menubar_memory = 0
            service_memory = 0

            # Get memory for menu bar app (current process)
            current_process = psutil.Process(os.getpid())
            menubar_memory = current_process.memory_info().rss / 1024 / 1024  # MB

            # Get memory for clipboard monitor service - use same logic as unified dashboard
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    cmdline = proc.info.get('cmdline', [])

                    # Skip current process (menu bar app)
                    if pid == os.getpid():
                        continue

                    # Use the same detection logic as unified dashboard
                    is_clipboard_process = False
                    cmdline_str = ""

                    if cmdline:
                        cmdline_str = ' '.join(cmdline).lower()
                        # More specific detection to avoid false positives
                        is_clipboard_process = (
                            'menu_bar_app.py' in cmdline_str or
                            ('main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                                'clipboard monitor', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                            ]))
                        )

                    # Also check by process name (for PyInstaller executables)
                    if not is_clipboard_process and name == 'ClipboardMonitor':
                        is_clipboard_process = True

                    # If this is a clipboard process, check if it's the main service
                    if is_clipboard_process:
                        is_main_service = False

                        if 'main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                            'clipboard', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                        ]):
                            is_main_service = True
                        elif name == 'ClipboardMonitor':
                            # For PyInstaller executables, use memory heuristic
                            memory_mb = proc.memory_info().rss / 1024 / 1024
                            if memory_mb <= 50:  # Main service typically uses less memory
                                is_main_service = True

                        if is_main_service:
                            service_memory = proc.memory_info().rss / 1024 / 1024  # MB
                            break

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # Update history for mini histograms
            self.menubar_history.append(menubar_memory)
            self.service_history.append(service_memory)

            if len(self.menubar_history) > 10: self.menubar_history.pop(0)
            if len(self.service_history) > 10: self.service_history.pop(0)

            self.menubar_peak = max(self.menubar_peak, menubar_memory)
            self.service_peak = max(self.service_peak, service_memory)

            menubar_histogram = self._generate_mini_histogram(self.menubar_history, self.menubar_peak)
            service_histogram = self._generate_mini_histogram(self.service_history, self.service_peak)

            self.memory_menubar_item.title = f"Menu Bar: {menubar_memory:.1f}MB {menubar_histogram} Peak: {self.menubar_peak:.0f}MB"
            self.memory_service_item.title = f"Service: {service_memory:.1f}MB  {service_histogram} Peak: {self.service_peak:.0f}MB"

        except Exception as e:
            self.memory_menubar_item.title = "Menu Bar: Error"
            self.memory_service_item.title = "Service: Error"
            try:
                import datetime
                with open(self.error_log_path, 'a') as f:
                    f.write(f"[{datetime.datetime.now()}] ERROR in update_memory_status: {str(e)}\n")
                    import traceback
                    f.write(f"  Traceback: {traceback.format_exc()}\n")
                    f.write("---\n")
            except:
                pass

    def _generate_mini_histogram(self, values, peak_value):
        """Generate mini histogram bars for memory visualization"""
        if not values:
            return "▁▁▁▁▁▁▁▁▁▁"

        # Ensure we have exactly 10 values
        if len(values) < 10:
            values = [0] * (10 - len(values)) + values
        else:
            values = values[-10:]

        # Normalize values to 0-7 range for Unicode block characters
        if peak_value > 0:
            normalized = [min(7, int((v / peak_value) * 7)) for v in values]
        else:
            normalized = [0] * 10

        # Unicode block characters for different heights
        bars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

        # Generate histogram with color coding
        histogram = ''.join([bars[level] for level in normalized])

        return histogram

    def _get_memory_color_indicator(self, current_mb, peak_mb):
        """Get color indicator based on memory usage"""
        if peak_mb == 0:
            return "🟢"

        usage_ratio = current_mb / peak_mb
        if usage_ratio < 0.5:
            return "🟢"  # Green - low usage
        elif usage_ratio < 0.8:
            return "🟡"  # Yellow - moderate usage
        else:
            return "🔴"  # Red - high usage





    def _is_process_running(self, process_name):
        """Check if a monitored process is running (system-wide check)"""
        # First check our tracked processes
        process = self._monitoring_processes.get(process_name)
        if process:
            try:
                if isinstance(process, int):
                    import os
                    os.kill(process, 0)  # Check if PID exists
                    return True
                else:
                    if process.poll() is None:
                        return True
            except:
                # Process died, remove from tracking
                del self._monitoring_processes[process_name]

        # System-wide check for dashboard processes
        script_names = {
            'visualizer': 'memory_visualizer.py',
            'dashboard': 'memory_monitoring_dashboard.py'
        }

        script_name = script_names.get(process_name)
        if not script_name:
            return False

        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and script_name in ' '.join(cmdline):
                        # Found existing process, track it
                        self._monitoring_processes[process_name] = proc.info['pid']
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

        return False

    def _kill_monitoring_process(self, process_name):
        """Kill a monitored process"""
        try:
            process = self._monitoring_processes.get(process_name)
            if process:
                try:
                    if isinstance(process, int):
                        # It's a PID
                        import os
                        import signal
                        os.kill(process, signal.SIGTERM)
                    else:
                        # It's a Popen object
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except:
                            process.kill()

                    # Remove from tracking
                    del self._monitoring_processes[process_name]
                    print(f"Killed monitoring process: {process_name}")

                except Exception as e:
                    print(f"Error killing process {process_name}: {e}")
                    # Remove from tracking anyway
                    if process_name in self._monitoring_processes:
                        del self._monitoring_processes[process_name]

            # Also try to kill by script name system-wide
            script_names = {
                'visualizer': 'memory_visualizer.py',
                'monitoring_dashboard': 'memory_monitoring_dashboard.py',
                'unified_dashboard': 'unified_memory_dashboard.py'
            }

            script_name = script_names.get(process_name)
            if script_name:
                try:
                    import psutil
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            cmdline = proc.info.get('cmdline', [])
                            if cmdline and script_name in ' '.join(cmdline):
                                proc_obj = psutil.Process(proc.info['pid'])
                                proc_obj.terminate()
                                print(f"Terminated system process for {script_name}")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except Exception as e:
                    print(f"Error during system-wide kill for {process_name}: {e}")

        except Exception as e:
            print(f"Error in _kill_monitoring_process for {process_name}: {e}")

    def show_mac_notification(self, title, subtitle, message):
        """Show a macOS notification using AppleScript for more reliability"""
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Escape quotes to prevent AppleScript injection
            title = title.replace('"', '\"')
            subtitle = subtitle.replace('"', '\"')
            message = message.replace('"', '\"')

            # Use AppleScript to show notification
            script = f'''
            display notification "{message}" with title "{title}" subtitle "{subtitle}"
            '''

            subprocess.run(["osascript", "-e", script], check=True)

            # Remove any ANSI color codes from notification log
            import re
            log_line = f"[{timestamp}] Notification sent: {title} - {subtitle} - {message}\n"
            ansi_escape = re.compile(r'\x1B\[[0-9;]*[mK]')
            log_line = ansi_escape.sub('', log_line)
            with open(self.log_path, 'a') as f:
                f.write(log_line)
        except Exception as e:
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Remove any ANSI color codes from error log
            import re
            log_line = f"[{timestamp}] Notification error: {str(e)}\n"
            ansi_escape = re.compile(r'\x1B\[[0-9;]*[mK]')
            log_line = ansi_escape.sub('', log_line)
            with open(self.error_log_path, 'a') as f:
                f.write(log_line)

    def _write_log_header_if_needed(self, log_path, header):
        """Write a header to the log file if it is empty."""
        if not os.path.exists(log_path) or os.path.getsize(log_path) == 0:
            with open(log_path, 'a') as f:
                f.write(header)

    LOG_HEADER = (
        "=== Clipboard Monitor Output Log ===\n"
        "Created: {date}\n"
        "Format: [YYYY-MM-DD HH:MM:SS] [LEVEL ] | Message\n"
        "-------------------------------------\n"
    ).format(date=__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    ERR_LOG_HEADER = (
        "=== Clipboard Monitor Error Log ===\n"
        "Created: {date}\n"
        "Format: [YYYY-MM-DD HH:MM:SS] [LEVEL ] | Message\n"
        "-------------------------------------\n"
    ).format(date=__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def log_event(self, message, level="INFO", section_separator=False):
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        padded_level = f"{level:<5}"
        log_line = f"[{timestamp}] [{padded_level}] | {message}\n"
        self._write_log_header_if_needed(self.log_path, self.LOG_HEADER)
        with open(self.log_path, 'a') as f:
            if section_separator:
                f.write("\n" + "-" * 60 + "\n")
            f.write(log_line)
            if section_separator:
                f.write("-" * 60 + "\n\n")
            f.flush()

    def log_error(self, message, multiline_details=None, section_separator=False):
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        padded_level = "ERROR"
        log_line = f"[{timestamp}] [{padded_level}] | {message}\n"
        self._write_log_header_if_needed(self.error_log_path, self.ERR_LOG_HEADER)
        with open(self.error_log_path, 'a') as f:
            if section_separator:
                f.write("\n" + "-" * 60 + "\n")
            f.write(log_line)
            if multiline_details:
                for line in multiline_details.splitlines():
                    f.write(f"    {line}\n")
            if section_separator:
                f.write("-" * 60 + "\n\n")
            f.flush()



# Export for test and import usage
class ClipboardMenuBarApp(ClipboardMonitorMenuBar):
    def open_web_viewer(self, _):
        """Open the web-based clipboard history viewer (for test compatibility)."""
        import subprocess
        import os
        web_viewer = os.path.join(os.path.dirname(__file__), 'web_history_viewer.py')
        if os.path.exists(web_viewer):
            subprocess.Popen(["/usr/bin/python3", web_viewer])
        else:
            subprocess.Popen(["open", os.path.expanduser("~/")])

    def open_cli_viewer(self, _):
        """Open the CLI clipboard history viewer (for test compatibility)."""
        import subprocess
        import os
        cli_viewer = os.path.join(os.path.dirname(__file__), 'cli_history_viewer.py')
        if os.path.exists(cli_viewer):
            subprocess.Popen(["/usr/bin/python3", cli_viewer])
        else:
            subprocess.Popen(["open", os.path.expanduser("~/")])
    def get_status_display(self):
        """Return a string representing the current service status for UI/tests."""
        from utils import get_app_paths
        paths = get_app_paths()
        status_file = paths.get("status_file")
        status = "unknown"
        if status_file and os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    status = f.read().strip()
            except Exception:
                status = "error"
        if status == "running_enhanced":
            return "🟢 Enhanced Mode"
        elif status == "running_polling":
            return "🟡 Polling Mode"
        elif status == "paused":
            return "⏸️ Paused"
        elif status == "error":
            return "🔴 Error"
        else:
            return "❓ Unknown"

    def copy_to_clipboard(self, content):
        """Copy the given content to the clipboard (for test compatibility)."""
        if PYPERCLIP_AVAILABLE:
            pyperclip.copy(content)
        else:
            print("Warning: pyperclip not available in this environment")

    def open_gui_viewer(self, _):
        """Open the GUI clipboard history viewer (for test compatibility)."""
        import subprocess
        from utils import get_app_paths

# Memory debugging imports
try:
    from memory_debugging import activate_memory_debugging, debug_timer_memory, log_memory
    MEMORY_DEBUG_AVAILABLE = True
    print("✅ Memory debugging enabled")
except ImportError as e:
    MEMORY_DEBUG_AVAILABLE = False
    print(f"⚠️  Memory debugging not available: {e}")

if __name__ == "__main__":
    ClipboardMonitorMenuBar().run()
