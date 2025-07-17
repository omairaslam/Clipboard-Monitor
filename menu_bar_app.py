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
import pyperclip

# Hide Dock icon for menu bar app
try:
    from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
    NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
except Exception:
    pass




class ClipboardMonitorMenuBar(rumps.App):
    def __init__(self):
        # Use a simple title with an emoji that works in the menu bar
        super().__init__("📋", quit_button=None)

        # Configuration
        self.config_manager = ConfigManager()
        self.home_dir = str(Path.home())
        self.plist_path = f"{self.home_dir}/Library/LaunchAgents/com.clipboardmonitor.plist"
        # Always use get_app_paths() for log paths
        paths = get_app_paths()
        self.log_path = paths["out_log"]
        self.error_log_path = paths["err_log"]
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
        self.polling_options = POLLING_INTERVALS
        self.enhanced_options = ENHANCED_CHECK_INTERVALS

        # Initialize menu components
        self._init_menu_items()
        self._init_submenus()
        self._init_preferences_menu()

        # Build the main menu structure
        self._build_main_menu()
        
        # Schedule initial history update and periodic status checks
        rumps.Timer(self.initial_history_update, 3).start()
        self.timer = threading.Thread(target=self.update_status_periodically)
        self.timer.daemon = True
        self.timer.start()

        # Start memory monitoring
        self.memory_timer = rumps.Timer(self.update_memory_status, 5)
        self.memory_timer.start()

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

        # Memory monitoring submenu (consolidated with memory usage items)
        self.memory_monitor_menu = rumps.MenuItem("Memory Monitor")
        self.memory_unified_dashboard_item = rumps.MenuItem("📊 Unified Dashboard", callback=self.start_unified_dashboard)
        self.memory_stats_item = rumps.MenuItem("📋 Memory Statistics", callback=self.show_memory_stats)
        self.memory_cleanup_item = rumps.MenuItem("🧹 Force Memory Cleanup", callback=self.force_memory_cleanup)

        # Memory tracking items (moved from Memory Usage menu)
        self.memory_trends_item = rumps.MenuItem("📈 View Memory Trends", callback=self.show_memory_trends)
        self.toggle_tracking_item = rumps.MenuItem("🔄 Start Memory Tracking", callback=self.toggle_memory_tracking)

        # Build memory monitor submenu
        self.memory_monitor_menu.add(self.memory_unified_dashboard_item)
        self.memory_monitor_menu.add(rumps.separator)
        self.memory_monitor_menu.add(self.memory_stats_item)
        self.memory_monitor_menu.add(self.memory_cleanup_item)
        self.memory_monitor_menu.add(rumps.separator)
        self.memory_monitor_menu.add(self.memory_trends_item)
        self.memory_monitor_menu.add(self.toggle_tracking_item)

        # Initialize monitoring processes tracking (moved from removed _init_memory_usage_menu)
        self._monitoring_processes = {}

        # Memory tracking data structures (moved from removed _init_memory_usage_menu)
        self.memory_data = {"menubar": [], "service": []}
        self.memory_timestamps = []
        self.memory_tracking_active = False

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
        # Update all menu items
        for item in sender.parent.itervalues():
            if isinstance(item, rumps.MenuItem):
                item.state = (item.title == sender.title)

        mode_map = {"New Tab": "_blank", "Same Tab": "_self"}
        new_mode = mode_map[sender.title]

        if set_config_value('modules', 'drawio_edit_mode', new_mode):
            rumps.notification("Clipboard Monitor", "Draw.io Edit Mode",
                              f"Edit mode set to {sender.title}")
            self.restart_service(None)
        else:
            rumps.notification("Error", "Failed to update Draw.io edit mode", "Could not save configuration")

    def set_drawio_appearance(self, sender):
        """Set Draw.io appearance."""
        # Update all menu items
        for item in sender.parent.itervalues():
            if isinstance(item, rumps.MenuItem):
                item.state = (item.title == sender.title)

        appearance_map = {"Auto": "auto", "Light": "light", "Dark": "dark"}
        new_appearance = appearance_map[sender.title]

        if set_config_value('modules', 'drawio_appearance', new_appearance):
            rumps.notification("Clipboard Monitor", "Draw.io Appearance",
                              f"Appearance set to {sender.title}")
            self.restart_service(None)
        else:
            rumps.notification("Error", "Failed to update Draw.io appearance", "Could not save configuration")

    def set_drawio_link_behavior(self, sender):
        """Set Draw.io link behavior."""
        # Update all menu items
        for item in sender.parent.itervalues():
            if isinstance(item, rumps.MenuItem):
                item.state = (item.title == sender.title)

        behavior_map = {"Auto": "auto", "New Tab": "blank", "Same Tab": "self"}
        new_behavior = behavior_map[sender.title]

        if set_config_value('modules', 'drawio_links', new_behavior):
            rumps.notification("Clipboard Monitor", "Draw.io Link Behavior",
                              f"Link behavior set to {sender.title}")
            self.restart_service(None)
        else:
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
        for name, value in self.polling_options.items():
            item = rumps.MenuItem(name, callback=self.set_polling_interval)
            item.state = (value == current_polling)
            polling_menu.add(item)
        return polling_menu

    def _create_enhanced_interval_menu(self):
        """Create the 'Enhanced Check Interval' submenu."""
        enhanced_menu = rumps.MenuItem("Enhanced Check Interval")
        current_enhanced = self.config_manager.get_config_value('general', 'enhanced_check_interval', 0.1)
        for name, value in self.enhanced_options.items():
            item = rumps.MenuItem(name, callback=self.set_enhanced_interval)
            item.state = (value == current_enhanced)
            enhanced_menu.add(item)
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
        drawio_menu = rumps.MenuItem("Draw.io Settings")

        # Copy Code option (restored)
        self.drawio_copy_code_item = rumps.MenuItem("Copy Code", callback=self.toggle_drawio_setting)
        self.drawio_copy_code_item.state = self.config_manager.get_config_value('modules', 'drawio_copy_code', True)
        drawio_menu.add(self.drawio_copy_code_item)

        # Copy URL option
        self.drawio_copy_url_item = rumps.MenuItem("Copy URL", callback=self.toggle_drawio_setting)
        self.drawio_copy_url_item.state = self.config_manager.get_config_value('modules', 'drawio_copy_url', True)
        drawio_menu.add(self.drawio_copy_url_item)

        # Open in Browser option
        self.drawio_open_browser_item = rumps.MenuItem("Open in Browser", callback=self.toggle_drawio_setting)
        self.drawio_open_browser_item.state = self.config_manager.get_config_value('modules', 'drawio_open_in_browser', True)
        drawio_menu.add(self.drawio_open_browser_item)

        # URL Parameters submenu (restored)
        drawio_menu.add(rumps.separator)
        drawio_menu.add(self._create_drawio_url_parameters_menu())

        return drawio_menu

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

        modes = [("New Tab", "_blank"), ("Same Tab", "_self")]
        for name, value in modes:
            item = rumps.MenuItem(name, callback=self.set_drawio_edit_mode)
            item.state = (value == current_mode)
            edit_mode_menu.add(item)

        return edit_mode_menu

    def _create_drawio_appearance_menu(self):
        """Create the 'Appearance' submenu for Draw.io."""
        appearance_menu = rumps.MenuItem("Appearance")
        current_appearance = self.config_manager.get_config_value('modules', 'drawio_appearance', 'auto')

        appearances = [("Auto", "auto"), ("Light", "light"), ("Dark", "dark")]
        for name, value in appearances:
            item = rumps.MenuItem(name, callback=self.set_drawio_appearance)
            item.state = (value == current_appearance)
            appearance_menu.add(item)

        return appearance_menu

    def _create_drawio_link_behavior_menu(self):
        """Create the 'Link Behavior' submenu for Draw.io."""
        link_menu = rumps.MenuItem("Link Behavior")
        current_behavior = self.config_manager.get_config_value('modules', 'drawio_links', 'auto')

        behaviors = [("Auto", "auto"), ("New Tab", "blank"), ("Same Tab", "self")]
        for name, value in behaviors:
            item = rumps.MenuItem(name, callback=self.set_drawio_link_behavior)
            item.state = (value == current_behavior)
            link_menu.add(item)

        return link_menu

    def _create_mermaid_settings_menu(self):
        """Create the 'Mermaid Settings' submenu."""
        mermaid_menu = rumps.MenuItem("Mermaid Settings")

        # Copy Code option (restored)
        self.mermaid_copy_code_item = rumps.MenuItem("Copy Code", callback=self.toggle_mermaid_setting)
        self.mermaid_copy_code_item.state = self.config_manager.get_config_value('modules', 'mermaid_copy_code', True)
        mermaid_menu.add(self.mermaid_copy_code_item)

        # Copy URL option
        self.mermaid_copy_url_item = rumps.MenuItem("Copy URL", callback=self.toggle_mermaid_setting)
        self.mermaid_copy_url_item.state = self.config_manager.get_config_value('modules', 'mermaid_copy_url', False)
        mermaid_menu.add(self.mermaid_copy_url_item)

        # Open in Browser option (restored)
        self.mermaid_open_browser_item = rumps.MenuItem("Open in Browser", callback=self.toggle_mermaid_setting)
        self.mermaid_open_browser_item.state = self.config_manager.get_config_value('modules', 'mermaid_open_in_browser', True)
        mermaid_menu.add(self.mermaid_open_browser_item)

        # Editor Theme submenu (restored)
        mermaid_menu.add(rumps.separator)
        mermaid_menu.add(self._create_mermaid_editor_theme_menu())

        return mermaid_menu

    def _create_mermaid_editor_theme_menu(self):
        """Create the 'Editor Theme' submenu for Mermaid."""
        theme_menu = rumps.MenuItem("Editor Theme")
        current_theme = self.config_manager.get_config_value('modules', 'mermaid_editor_theme', 'default')

        themes = [("Default", "default"), ("Dark", "dark"), ("Forest", "forest"), ("Neutral", "neutral")]
        for name, value in themes:
            item = rumps.MenuItem(name, callback=self.set_mermaid_editor_theme)
            item.state = (value == current_theme)
            theme_menu.add(item)

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

        memory_menu.add(rumps.separator)

        # Memory Statistics and Cleanup
        memory_menu.add(rumps.MenuItem("📋 Memory Statistics", callback=self.show_memory_stats))
        memory_menu.add(rumps.MenuItem("🧹 Force Memory Cleanup", callback=self.force_memory_cleanup))

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
        # Update all menu items
        for item in sender.parent.itervalues():
            if isinstance(item, rumps.MenuItem):
                item.state = (item.title == sender.title)

        theme_map = {"Default": "default", "Dark": "dark", "Forest": "forest", "Neutral": "neutral"}
        new_theme = theme_map[sender.title]

        if set_config_value('modules', 'mermaid_editor_theme', new_theme):
            rumps.notification("Clipboard Monitor", "Mermaid Editor Theme",
                              f"Editor theme set to {sender.title}")
            self.restart_service(None)
        else:
            rumps.notification("Error", "Failed to update Mermaid editor theme", "Could not save configuration")

    def _build_main_menu(self):
        """Build the main menu structure to match docs/MENU_ORGANIZATION.md."""
        # Section 1: Status & Service Control
        self.menu.add(self.status_item)
        self.menu.add(self.memory_menubar_item)  # Memory visualization line 1
        self.menu.add(self.memory_service_item)  # Memory visualization line 2
        self.menu.add(rumps.separator)
        self.menu.add(self.pause_toggle)
        self.menu.add(self.service_control_menu)
        self.menu.add(rumps.separator)

        # Section 2: History & Modules (as per docs: History items first, then Modules)
        self.menu.add(self.recent_history_menu)
        self.menu.add(self.history_menu)
        self.menu.add(self.module_menu)
        self.menu.add(rumps.separator)

        # Memory monitoring tools (consolidated section)
        self.menu.add(self.memory_monitor_menu)
        self.menu.add(rumps.separator)

        # Section 3: Preferences
        self.menu.add(self.prefs_menu)
        self.menu.add(rumps.separator)

        # Section 4: Application (Logs then Quit)
        self.menu.add(self.logs_menu)
        self.menu.add(self.quit_item)
    
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
    
    def update_status(self):
        """Check if the service is running and update the status menu item"""
        try:
            # Check if the process is running using launchctl
            result = subprocess.run(
                ["launchctl", "list", "com.clipboardmonitor"],
                capture_output=True, 
                text=True
            )
            
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
        # Update all menu items
        for item in sender.parent.itervalues():
            if isinstance(item, rumps.MenuItem):
                item.state = (item.title == sender.title)

        # Get the new interval value
        new_interval = self.enhanced_options[sender.title]

        if set_config_value('general', 'enhanced_check_interval', new_interval):
            rumps.notification("Clipboard Monitor", "Enhanced Check Interval",
                              f"Enhanced check interval set to {new_interval} seconds")
            self.restart_service(None)
        else:
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
        # Update all menu items
        for item in sender.parent.itervalues():
            if isinstance(item, rumps.MenuItem):
                item.state = (item.title == sender.title)

        # Get the new interval value
        new_interval = self.polling_options[sender.title]

        if set_config_value('general', 'polling_interval', new_interval):
            rumps.notification("Clipboard Monitor", "Polling Interval",
                              f"Polling interval set to {new_interval} seconds")
            self.restart_service(None)
        else:
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

    def initial_history_update(self, _):
        """Initial history menu update - called once on startup"""
        self.update_recent_history_menu()
        # Set up periodic updates using rumps Timer (runs on main thread)
        self.history_timer = rumps.Timer(self.periodic_history_update, 30)
        self.history_timer.start()

    def periodic_history_update(self, _):
        """Periodic history menu update - called every 30 seconds on main thread"""
        self.update_recent_history_menu()

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
                    pyperclip.copy(content_to_copy)
                    truncated = content_to_copy[:50] + '...' if len(content_to_copy) > 50 else content_to_copy # Use centralized notification
                    show_notification("Clipboard", "Item Copied", f"Copied: {truncated}", self.log_path, self.error_log_path)
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
                        test_python = '/usr/bin/python3'
                        if not os.path.exists(test_python):
                            for alt_python in ['/usr/local/bin/python3', '/opt/homebrew/bin/python3']:
                                if os.path.exists(alt_python):
                                    test_python = alt_python
                                    break

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

                # For PyInstaller bundles, we need to use the system Python since the dashboard
                # script is a separate Python file, not a bundled executable
                if getattr(sys, 'frozen', False):
                    # We're in a PyInstaller bundle, use system Python
                    python_executable = '/usr/bin/python3'
                    # Also try common Python locations if /usr/bin/python3 doesn't exist
                    if not os.path.exists(python_executable):
                        for alt_python in ['/usr/local/bin/python3', '/opt/homebrew/bin/python3']:
                            if os.path.exists(alt_python):
                                python_executable = alt_python
                                break

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

                # Open browser
                webbrowser.open('http://localhost:8001')

                rumps.notification("Unified Memory Dashboard", "Started Successfully",
                                 "Comprehensive monitoring available at localhost:8001")
            else:
                rumps.alert("Unified Dashboard not found",
                           f"The unified_memory_dashboard.py file was not found.\nSearched paths:\n{script_path}")

        except Exception as e:
            rumps.alert("Error", f"Failed to start Unified Memory Dashboard: {e}")

    def _auto_start_dashboard(self):
        """Auto-start unified dashboard on app launch (silent, no browser opening)"""
        try:
            import subprocess
            import time
            import os

            # Write debug to file since print doesn't work in PyInstaller
            with open('/tmp/clipboard_debug.log', 'a') as f:
                f.write(f"DEBUG: _auto_start_dashboard called at {time.time()}\n")
            print("DEBUG: _auto_start_dashboard called")

            # PROTECTION: Check if we're already being launched by a dashboard process
            # This prevents recursive spawning
            current_cmdline = ' '.join(sys.argv)
            if '--auto-start' in current_cmdline or 'unified_memory_dashboard.py' in current_cmdline:
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

            # For bundled app, try alternative paths
            if not os.path.exists(script_path):
                script_path = os.path.join(os.path.dirname(__file__), '..', 'Resources', 'unified_memory_dashboard.py')
            if not os.path.exists(script_path):
                script_path = os.path.join(os.path.dirname(__file__), '..', 'Frameworks', 'unified_memory_dashboard.py')

            if os.path.exists(script_path):
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

                print(f"DEBUG: Using Python executable: {python_executable}")
                print(f"DEBUG: Starting dashboard with command: {python_executable} {script_path} --auto-start")

                proc = subprocess.Popen([python_executable, script_path, '--auto-start'], env=env)
                self._monitoring_processes['unified_dashboard'] = proc

                print("Auto-started unified dashboard (5-minute timeout)")

                # Show subtle notification
                rumps.notification("Clipboard Monitor", "Dashboard Auto-Started",
                                 "Memory monitoring available at localhost:8001 (5min timeout)")
            else:
                print(f"DEBUG: Unified dashboard script not found at: {script_path}")
                print("Unified dashboard script not found, skipping auto-start")

        except Exception as e:
            print(f"Error auto-starting unified dashboard: {e}")
            # Don't show error to user for auto-start failures

    def show_memory_stats(self, sender):
        """Show comprehensive memory statistics for debugging"""
        try:
            import psutil
            import gc
            import os
            import threading
            from datetime import datetime

            # Format memory sizes
            def format_bytes(bytes_val):
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if bytes_val < 1024.0:
                        return f"{bytes_val:.1f} {unit}"
                    bytes_val /= 1024.0
                return f"{bytes_val:.1f} TB"

            # Get current process (menu bar app) memory info
            current_process = psutil.Process()
            current_memory = current_process.memory_info()
            current_percent = current_process.memory_percent()

            # Find all clipboard-related processes
            clipboard_processes = []
            total_clipboard_memory = 0

            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent', 'create_time', 'status']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline:
                        cmdline_str = ' '.join(cmdline).lower()

                        # Enhanced detection for clipboard processes
                        is_clipboard_process = any(keyword in cmdline_str for keyword in [
                            'clipboard', 'menu_bar_app', 'main.py', 'unified_memory_dashboard'
                        ]) or (
                            'python' in proc.info['name'].lower() and
                            any(path_part in cmdline_str for path_part in [
                                'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                            ])
                        )

                        if is_clipboard_process:
                            memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                            total_clipboard_memory += memory_mb

                            # Determine process type
                            process_type = "unknown"
                            if 'menu_bar_app.py' in cmdline_str:
                                process_type = "menu_bar"
                            elif 'main.py' in cmdline_str and any(path_part in cmdline_str for path_part in [
                                'clipboard', 'clipboardmonitor', 'clipboard-monitor', 'clipboard_monitor'
                            ]):
                                process_type = "main_service"
                            elif 'unified_memory_dashboard.py' in cmdline_str:
                                process_type = "dashboard"

                            clipboard_processes.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'type': process_type,
                                'memory_mb': memory_mb,
                                'cpu_percent': proc.info['cpu_percent'] or 0,
                                'status': proc.info['status'],
                                'create_time': datetime.fromtimestamp(proc.info['create_time']).strftime('%H:%M:%S'),
                                'is_current': proc.info['pid'] == current_process.pid
                            })

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # Get system memory info
            system_memory = psutil.virtual_memory()
            swap_memory = psutil.swap_memory()

            # Get CPU info
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)

            # Force garbage collection and get detailed stats
            collected = gc.collect()
            gc_stats = gc.get_stats()
            gc_counts = gc.get_count()
            gc_thresholds = gc.get_threshold()

            # Memory tracking stats
            tracking_status = "Active" if self.memory_tracking_active else "Inactive"
            tracking_points = len(self.memory_data.get("menubar", []))
            peak_menubar = self.menubar_peak
            peak_service = self.service_peak

            # Thread information
            thread_count = threading.active_count()
            main_thread = threading.main_thread()
            current_thread = threading.current_thread()

            # Build comprehensive stats message
            stats_message = f"""🔍 COMPREHENSIVE MEMORY DIAGNOSTICS

📊 CLIPBOARD PROCESSES ({len(clipboard_processes)} found):"""

            for proc in clipboard_processes:
                current_marker = " ← CURRENT" if proc['is_current'] else ""
                stats_message += f"""
• {proc['type'].upper()}: PID {proc['pid']} ({proc['status']})
  Memory: {proc['memory_mb']:.1f} MB | CPU: {proc['cpu_percent']:.1f}%
  Started: {proc['create_time']}{current_marker}"""

            stats_message += f"""

💾 CURRENT PROCESS DETAILS:
• RSS: {format_bytes(current_memory.rss)} (Physical RAM)
• VMS: {format_bytes(current_memory.vms)} (Virtual Memory)
• Percent: {current_percent:.2f}% of system memory
• PID: {current_process.pid}
• Threads: {thread_count} active threads

📈 MEMORY TRACKING:
• Status: {tracking_status}
• Data Points: {tracking_points}
• Menu Bar Peak: {peak_menubar:.1f} MB
• Service Peak: {peak_service:.1f} MB
• Total Clipboard Memory: {total_clipboard_memory:.1f} MB

🖥️  SYSTEM RESOURCES:
• RAM Total: {format_bytes(system_memory.total)}
• RAM Available: {format_bytes(system_memory.available)} ({100-system_memory.percent:.1f}% free)
• RAM Used: {format_bytes(system_memory.used)} ({system_memory.percent:.1f}%)
• Swap Total: {format_bytes(swap_memory.total)}
• Swap Used: {format_bytes(swap_memory.used)} ({swap_memory.percent:.1f}%)

⚡ CPU & PERFORMANCE:
• CPU Cores: {cpu_count}
• CPU Usage: {cpu_percent:.1f}%
• Load Average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}

🗑️  GARBAGE COLLECTION:
• Objects Collected: {collected}
• Gen 0: {gc_counts[0]} objects (threshold: {gc_thresholds[0]})
• Gen 1: {gc_counts[1]} objects (threshold: {gc_thresholds[1]})
• Gen 2: {gc_counts[2]} objects (threshold: {gc_thresholds[2]})
• Collections: G0:{gc_stats[0]['collections']}, G1:{gc_stats[1]['collections']}, G2:{gc_stats[2]['collections']}

🧵 THREADING INFO:
• Active Threads: {thread_count}
• Main Thread: {main_thread.name} ({'alive' if main_thread.is_alive() else 'dead'})
• Current Thread: {current_thread.name}

⏰ TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

            rumps.alert("Memory Diagnostics", stats_message)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            rumps.alert("Diagnostics Error", f"Failed to get memory diagnostics:\n\n{str(e)}\n\nDetails:\n{error_details[:500]}...")

    def force_memory_cleanup(self, sender):
        """Force garbage collection and memory cleanup"""
        try:
            import gc
            import psutil

            # Get memory before cleanup
            process = psutil.Process()
            memory_before = process.memory_info().rss

            # Force garbage collection
            collected = gc.collect()

            # Get memory after cleanup
            memory_after = process.memory_info().rss
            memory_freed = memory_before - memory_after

            def format_bytes(bytes_val):
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if bytes_val < 1024.0:
                        return f"{bytes_val:.1f} {unit}"
                    bytes_val /= 1024.0
                return f"{bytes_val:.1f} TB"

            if memory_freed > 0:
                message = f"Memory cleanup completed!\n\nObjects collected: {collected}\nMemory freed: {format_bytes(memory_freed)}"
            else:
                message = f"Memory cleanup completed!\n\nObjects collected: {collected}\nNo significant memory freed"

            rumps.notification("Memory Cleanup", "Completed", message)

        except Exception as e:
            rumps.alert("Error", f"Failed to perform memory cleanup: {e}")

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

    def update_memory_status(self, _):
        """Update the memory status in the menu."""
        try:
            import psutil

            # Get memory for menu bar app (current process)
            menubar_process = psutil.Process(os.getpid())
            menubar_memory = menubar_process.memory_info().rss / 1024 / 1024  # MB

            # Get memory for clipboard monitor service
            service_memory = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline:
                        # Check for PyInstaller-built main service executable
                        cmdline_str = ' '.join(cmdline) if cmdline else ''
                        # More specific matching for the main service
                        if (('ClipboardMonitor.app/Contents/MacOS/ClipboardMonitor' in cmdline_str and
                             'MenuBar' not in cmdline_str) or
                            ('main.py' in cmdline_str and 'menu_bar_app.py' not in cmdline_str)):
                            if proc.pid != os.getpid():  # Not the menu bar app
                                service_memory = proc.memory_info().rss / 1024 / 1024  # MB
                                break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, AttributeError):
                    pass

            # Update history for mini histograms
            self.menubar_history.append(menubar_memory)
            self.service_history.append(service_memory)

            # Keep only last 10 values
            if len(self.menubar_history) > 10:
                self.menubar_history = self.menubar_history[-10:]
            if len(self.service_history) > 10:
                self.service_history = self.service_history[-10:]

            # Update peak values
            if menubar_memory > self.menubar_peak:
                self.menubar_peak = menubar_memory
            if service_memory > self.service_peak:
                self.service_peak = service_memory

            # Generate mini histograms
            menubar_histogram = self._generate_mini_histogram(self.menubar_history, self.menubar_peak)
            service_histogram = self._generate_mini_histogram(self.service_history, self.service_peak)

            # Memory status removed - consolidated into Memory Monitor menu

            # Update main menu display items (two separate lines)
            self.memory_menubar_item.title = f"Menu Bar: {menubar_memory:.1f}MB {menubar_histogram} Peak: {self.menubar_peak:.0f}MB"
            self.memory_service_item.title = f"Service: {service_memory:.1f}MB  {service_histogram} Avg: {sum(self.service_history)/len(self.service_history) if self.service_history else 0:.0f}MB"

            # Record data if tracking is active
            if self.memory_tracking_active:
                self.memory_data["menubar"].append(menubar_memory)
                self.memory_data["service"].append(service_memory)
                self.memory_timestamps.append(time.time())

                # Limit data points to prevent excessive memory usage
                max_points = 1000
                if len(self.memory_timestamps) > max_points:
                    self.memory_timestamps = self.memory_timestamps[-max_points:]
                    self.memory_data["menubar"] = self.memory_data["menubar"][-max_points:]
                    self.memory_data["service"] = self.memory_data["service"][-max_points:]

        except Exception:
            # Memory status removed - error handling simplified
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

    def toggle_memory_tracking(self, sender):
        """Toggle detailed memory tracking for trends."""
        self.memory_tracking_active = not self.memory_tracking_active

        if self.memory_tracking_active:
            sender.title = "🛑 Stop Memory Tracking"
            # Clear previous data
            self.memory_data = {"menubar": [], "service": []}
            self.memory_timestamps = []
            rumps.notification("Memory Tracking", "Started",
                              "Memory usage is now being recorded for trend analysis.")
        else:
            sender.title = "🔄 Start Memory Tracking"
            rumps.notification("Memory Tracking", "Stopped",
                              "Memory tracking has been stopped.")

    def show_memory_trends(self, _):
        """Generate and display memory usage trends."""
        if not self.memory_data["menubar"] or not self.memory_timestamps:
            rumps.notification("Memory Trends", "No Data",
                              "Start memory tracking first to collect data.")
            return

        try:
            import tempfile

            # Create a temporary HTML file with the chart
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
                html_path = f.name

                # Generate timestamps for x-axis
                timestamps = [time.strftime('%H:%M:%S', time.localtime(ts)) for ts in self.memory_timestamps]

                # Create HTML with embedded chart using Chart.js
                html_content = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Clipboard Monitor Memory Usage</title>
                    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        .container {{ max-width: 1200px; margin: 0 auto; }}
                        .chart-container {{ position: relative; height: 400px; margin: 20px 0; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Clipboard Monitor Memory Usage Trends</h1>
                        <div class="chart-container">
                            <canvas id="memoryChart"></canvas>
                        </div>
                    </div>
                    <script>
                        const ctx = document.getElementById('memoryChart').getContext('2d');
                        const chart = new Chart(ctx, {{
                            type: 'line',
                            data: {{
                                labels: {timestamps},
                                datasets: [{{
                                    label: 'Menu Bar App (MB)',
                                    data: {self.memory_data["menubar"]},
                                    borderColor: 'rgb(75, 192, 192)',
                                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                    tension: 0.1
                                }}, {{
                                    label: 'Main Service (MB)',
                                    data: {self.memory_data["service"]},
                                    borderColor: 'rgb(255, 99, 132)',
                                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                                    tension: 0.1
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                maintainAspectRatio: false,
                                scales: {{
                                    y: {{
                                        beginAtZero: true,
                                        title: {{
                                            display: true,
                                            text: 'Memory Usage (MB)'
                                        }}
                                    }},
                                    x: {{
                                        title: {{
                                            display: true,
                                            text: 'Time'
                                        }}
                                    }}
                                }}
                            }}
                        }});
                    </script>
                </body>
                </html>
                '''

                f.write(html_content.encode())

            # Open the HTML file in the default browser
            webbrowser.open(f'file://{html_path}')

            rumps.notification("Memory Trends", "Chart Generated",
                              "Memory usage chart opened in your browser.")

        except Exception as e:
            rumps.alert("Error", f"Failed to generate memory trends: {e}")

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
        import pyperclip
        pyperclip.copy(content)

    def open_gui_viewer(self, _):
        """Open the GUI clipboard history viewer (for test compatibility)."""
        import subprocess
        from utils import get_app_paths
        paths = get_app_paths()
        history_file = paths.get("history_file")
        # For test, just open the history file in the default app
        if history_file and os.path.exists(history_file):
            subprocess.Popen(["open", history_file])
        else:
            subprocess.Popen(["open", os.path.expanduser("~/")])

ClipboardMenuBarApp = ClipboardMenuBarApp

if __name__ == "__main__":
    ClipboardMonitorMenuBar().run()
