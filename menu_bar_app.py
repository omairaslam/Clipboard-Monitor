#!/usr/bin/env python3
import rumps
import subprocess
import threading
import os
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
        self.plist_path = f"{self.home_dir}/Library/LaunchAgents/com.omairaslam.clipboardmonitor.plist"
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
        # self._build_main_menu() # TEMP: Commented out for StopIteration debug
        
        # Schedule initial history update and periodic status checks
        # rumps.Timer(self.initial_history_update, 3).start() # TEMP: Commented out
        # self.timer = threading.Thread(target=self.update_status_periodically) # TEMP: Commented out
        # self.timer.daemon = True
        # self.timer.start()

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
        
    def toggle_drawio_url_behavior_setting(self, sender):
        """Toggle Draw.io URL behavior settings like 'Copy URL' or 'Open in Browser'."""
        sender.state = not sender.state
        
        setting_map = {
            "Copy URL": "drawio_copy_url",
            "Open in Browser": "drawio_open_in_browser",
        }
        config_key = setting_map.get(sender.title)

        if config_key:
            if set_config_value('modules', config_key, sender.state):
                rumps.notification("Clipboard Monitor", "Draw.io Setting",
                                  f"{sender.title} behavior is now {'enabled' if sender.state else 'disabled'}.")
                self.restart_service(None) # Restart to apply changes if needed by module logic
            else:
                rumps.notification("Error", "Failed to update Draw.io setting", "Could not save configuration.")
        else:
            rumps.notification("Error", "Unknown Draw.io Setting", f"No configuration key found for '{sender.title}'.")

    def toggle_drawio_url_param_setting(self, sender):
        """Toggle Draw.io URL parameter settings like 'Lightbox', 'Layers', 'Navigation'."""
        sender.state = not sender.state

        setting_map = {
            "Lightbox": "drawio_lightbox",
            "Layers Enabled": "drawio_layers", # Updated title
            "Navigation Enabled": "drawio_nav", # Updated title
        }
        config_key = setting_map.get(sender.title)

        if config_key:
            if set_config_value('modules', config_key, sender.state):
                rumps.notification("Clipboard Monitor", "Draw.io URL Parameter",
                                  f"{sender.title} is now {'enabled' if sender.state else 'disabled'}.")
                self.restart_service(None) # Restart as URL construction changes
            else:
                rumps.notification("Error", "Failed to update Draw.io URL parameter", "Could not save configuration.")
        else:
            rumps.notification("Error", "Unknown Draw.io Parameter", f"No configuration key found for '{sender.title}'.")

    def set_drawio_edit_mode(self, sender):
        """Set the Draw.io edit mode."""
        new_mode_value = sender._edit_mode_value # Get value stored during menu creation

        # Update state for all items in the submenu
        for item_title, item_obj in sender.parent.items():
            if isinstance(item_obj, rumps.MenuItem): # Ensure it's a menu item
                 item_obj.state = (item_obj.title == sender.title)

        if set_config_value('modules', 'drawio_edit_mode', new_mode_value):
            rumps.notification("Clipboard Monitor", "Draw.io Edit Mode",
                              f"Edit mode set to: {sender.title}")
            self.restart_service(None) # Restart as URL construction changes
        else:
            rumps.notification("Error", "Failed to update Draw.io edit mode", "Could not save configuration.")

    def set_drawio_appearance(self, sender):
        """Set the Draw.io appearance mode."""
        new_appearance_value = sender._appearance_value
        for item_title, item_obj in sender.parent.items():
            if isinstance(item_obj, rumps.MenuItem):
                item_obj.state = (item_obj.title == sender.title)

        if set_config_value('modules', 'drawio_appearance', new_appearance_value):
            rumps.notification("Clipboard Monitor", "Draw.io Appearance", f"Appearance set to: {sender.title}")
            self.restart_service(None)
        else:
            rumps.notification("Error", "Failed to update Draw.io appearance", "Could not save configuration.")

    def set_drawio_links_mode(self, sender):
        """Set the Draw.io links mode."""
        new_links_value = sender._links_value
        for item_title, item_obj in sender.parent.items():
            if isinstance(item_obj, rumps.MenuItem):
                item_obj.state = (item_obj.title == sender.title)

        if set_config_value('modules', 'drawio_links', new_links_value):
            rumps.notification("Clipboard Monitor", "Draw.io Link Behavior", f"Link behavior set to: {sender.title}")
            self.restart_service(None)
        else:
            rumps.notification("Error", "Failed to update Draw.io link behavior", "Could not save configuration.")

    def set_drawio_border_color(self, _):
        """Set Draw.io border color via text input."""
        current_color = self.config_manager.get_config_value('modules', 'drawio_border_color', 'none')
        response = rumps.Window(
            message="Enter border color (e.g., FF0000 or 'none'):",
            title="Set Draw.io Border Color",
            default_text=current_color,
            ok="Set",
            cancel="Cancel",
            dimensions=(320, 20) # Adjusted width for longer message
        ).run()

        if response.clicked:
            new_color = response.text.strip()
            if not new_color: # User cleared the input, treat as "none" or default
                new_color = "none"

            # Basic validation: 'none' or hex (3, 6, 8 digits for RRGGBBAA)
            import re
            if new_color.lower() == "none" or re.fullmatch(r"^[0-9a-fA-F]{3}([0-9a-fA-F]{3})?([0-9a-fA-F]{2})?$", new_color):
                if set_config_value('modules', 'drawio_border_color', new_color):
                    rumps.notification("Clipboard Monitor", "Draw.io Border Color", f"Border color set to: {new_color}")
                    self.restart_service(None)
                else:
                    rumps.notification("Error", "Failed to update Draw.io border color", "Could not save configuration.")
            else:
                rumps.notification("Error", "Invalid Color", "Please enter 'none' or a valid hex color code (e.g., FF0000).")

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
        self.drawio_copy_url_item = rumps.MenuItem("Copy URL", callback=self.toggle_drawio_url_behavior_setting)
        self.drawio_copy_url_item.state = self.config_manager.get_config_value('modules', 'drawio_copy_url', True)
        drawio_menu.add(self.drawio_copy_url_item)

        self.drawio_open_browser_item = rumps.MenuItem("Open in Browser", callback=self.toggle_drawio_url_behavior_setting)
        self.drawio_open_browser_item.state = self.config_manager.get_config_value('modules', 'drawio_open_in_browser', True)
        drawio_menu.add(self.drawio_open_browser_item)

        drawio_menu.add(rumps.separator)

        # URL Parameters
        url_params_menu = rumps.MenuItem("URL Parameters")

        self.drawio_lightbox_item = rumps.MenuItem("Lightbox", callback=self.toggle_drawio_url_param_setting)
        self.drawio_lightbox_item.state = self.config_manager.get_config_value('modules', 'drawio_lightbox', True)
        url_params_menu.add(self.drawio_lightbox_item)

        # Edit Mode submenu
        edit_mode_submenu = rumps.MenuItem("Edit Mode")
        current_edit_mode = self.config_manager.get_config_value('modules', 'drawio_edit_mode', '_blank')
        from constants import DRAWIO_EDIT_MODES, DRAWIO_APPEARANCE_MODES, DRAWIO_LINKS_MODES # Import for menu creation
        for mode_name, mode_value in DRAWIO_EDIT_MODES.items():
            item = rumps.MenuItem(mode_name, callback=self.set_drawio_edit_mode)
            item.state = (mode_value == current_edit_mode)
            item._edit_mode_value = mode_value # Store actual value
            edit_mode_submenu.add(item)
        url_params_menu.add(edit_mode_submenu)

        self.drawio_layers_item = rumps.MenuItem("Layers Enabled", callback=self.toggle_drawio_url_param_setting)
        self.drawio_layers_item.state = self.config_manager.get_config_value('modules', 'drawio_layers', True)
        url_params_menu.add(self.drawio_layers_item)

        self.drawio_nav_item = rumps.MenuItem("Navigation Enabled", callback=self.toggle_drawio_url_param_setting)
        self.drawio_nav_item.state = self.config_manager.get_config_value('modules', 'drawio_nav', True)
        url_params_menu.add(self.drawio_nav_item)

        # Appearance submenu
        appearance_submenu = rumps.MenuItem("Appearance")
        current_appearance = self.config_manager.get_config_value('modules', 'drawio_appearance', 'auto')
        for appearance_name, appearance_value in DRAWIO_APPEARANCE_MODES.items():
            item = rumps.MenuItem(appearance_name, callback=self.set_drawio_appearance)
            item.state = (appearance_value == current_appearance)
            item._appearance_value = appearance_value
            appearance_submenu.add(item)
        url_params_menu.add(appearance_submenu)

        # Link Behavior submenu
        links_submenu = rumps.MenuItem("Link Behavior")
        current_links_mode = self.config_manager.get_config_value('modules', 'drawio_links', 'auto')
        for links_name, links_value in DRAWIO_LINKS_MODES.items():
            item = rumps.MenuItem(links_name, callback=self.set_drawio_links_mode)
            item.state = (links_value == current_links_mode)
            item._links_value = links_value
            links_submenu.add(item)
        url_params_menu.add(links_submenu)

        url_params_menu.add(rumps.MenuItem("Set Border Color...", callback=self.set_drawio_border_color))

        drawio_menu.add(url_params_menu)
        return drawio_menu

    def _create_mermaid_settings_menu(self):
        """Create the 'Mermaid Settings' submenu."""
        mermaid_menu = rumps.MenuItem("Mermaid Settings")
        self.mermaid_copy_url_item = rumps.MenuItem("Copy URL", callback=self.toggle_mermaid_setting)
        self.mermaid_copy_url_item.state = self.config_manager.get_config_value('modules', 'mermaid_copy_url', False)
        mermaid_menu.add(self.mermaid_copy_url_item)

        self.mermaid_open_browser_item = rumps.MenuItem("Open in Browser", callback=self.toggle_mermaid_setting)
        self.mermaid_open_browser_item.state = self.config_manager.get_config_value('modules', 'mermaid_open_in_browser', True) # Default True
        mermaid_menu.add(self.mermaid_open_browser_item)

        mermaid_menu.add(rumps.separator)

        # Mermaid Theme submenu
        theme_submenu = rumps.MenuItem("Editor Theme")
        current_theme = self.config_manager.get_config_value('modules', 'mermaid_theme', 'default')
        from constants import MERMAID_THEMES # Import for menu creation
        for theme_name, theme_value in MERMAID_THEMES.items():
            item = rumps.MenuItem(theme_name, callback=self.set_mermaid_theme)
            item.state = (theme_value == current_theme)
            item._theme_value = theme_value # Store actual value
            theme_submenu.add(item)
        mermaid_menu.add(theme_submenu)

        return mermaid_menu

    def _create_module_settings_menu(self):
        """Create the 'Module Settings' submenu."""
        module_menu = rumps.MenuItem("Module Settings")
        # Clipboard modification menu is now under Security Settings
        module_menu.add(self._create_drawio_settings_menu())
        module_menu.add(self._create_mermaid_settings_menu())

        # If no other module-specific settings are present, indicate this
        if not module_menu.values(): # Check if any items were added
            module_menu.add(rumps.MenuItem("(No specific module settings)", callback=None))
            # Disable the main "Module Settings" menu item if it's empty or just has the placeholder
            # This requires a way to access the parent menu item from _init_preferences_menu,
            # or restructuring how it's added. For now, we'll leave it clickable.
            # A simpler approach is to not add it to prefs_menu if it would be empty.
            # However, for now, let's keep it and it will show the placeholder.

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
        self.memory_optimization = rumps.MenuItem("Memory Optimization", callback=self.toggle_performance_setting)
        self.memory_optimization.state = self.config_manager.get_config_value('performance', 'memory_optimization', True)
        perf_menu.add(self.memory_optimization)
        self.process_large_content = rumps.MenuItem("Process Large Content", callback=self.toggle_performance_setting)
        self.process_large_content.state = self.config_manager.get_config_value('performance', 'process_large_content', True)
        perf_menu.add(self.process_large_content)
        perf_menu.add(rumps.MenuItem("Set Max Execution Time...", callback=self.set_max_execution_time))
        return perf_menu

    def _create_security_settings_menu(self):
        """Create the 'Security Settings' submenu."""
        security_menu = rumps.MenuItem("Security Settings")
        self.sanitize_clipboard = rumps.MenuItem("Sanitize Clipboard", callback=self.toggle_security_setting)
        self.sanitize_clipboard.state = self.config_manager.get_config_value('security', 'sanitize_clipboard', True)
        security_menu.add(self.sanitize_clipboard)
        security_menu.add(rumps.MenuItem("Set Max Clipboard Size...", callback=self.set_max_clipboard_size))
        security_menu.add(rumps.separator)
        security_menu.add(self._create_clipboard_modification_menu())  # Moved here
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
        return advanced_menu

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
            "Copy URL": "mermaid_copy_url",
            "Open in Browser": "mermaid_open_in_browser"
        }
        
        config_key = setting_map.get(sender.title)
        if config_key:
            if set_config_value('modules', config_key, sender.state):
                rumps.notification("Clipboard Monitor", "Mermaid Setting",
                                  f"{sender.title} is now {'enabled' if sender.state else 'disabled'}")
                self.restart_service(None) # Restart service to apply changes
            else:
                rumps.notification("Error", "Failed to update Mermaid setting", "Could not save configuration")

    def set_mermaid_theme(self, sender):
        """Set the Mermaid Live editor theme."""
        new_theme_value = sender._theme_value # Get value stored during menu creation

        # Update state for all items in the submenu
        for item_title, item_obj in sender.parent.items():
            if isinstance(item_obj, rumps.MenuItem): # Ensure it's a menu item
                item_obj.state = (item_obj.title == sender.title)

        if set_config_value('modules', 'mermaid_theme', new_theme_value):
            rumps.notification("Clipboard Monitor", "Mermaid Theme",
                              f"Editor theme set to: {sender.title}")
            self.restart_service(None) # Restart as URL construction changes
        else:
            rumps.notification("Error", "Failed to update Mermaid theme", "Could not save configuration.")
 
    def _build_main_menu(self):
        """Build the main menu structure to match docs/MENU_ORGANIZATION.md."""
        # Section 1: Status & Service Control
        self.menu.add(self.status_item)
        self.menu.add(rumps.separator)
        self.menu.add(self.pause_toggle)
        self.menu.add(self.service_control_menu)
        self.menu.add(rumps.separator)

        # Section 2: History & Modules (as per docs: History items first, then Modules)
        self.menu.add(self.recent_history_menu)
        self.menu.add(self.history_menu)
        self.menu.add(self.module_menu)
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
                ["launchctl", "list", "com.omairaslam.clipboardmonitor"], 
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
            "Memory Optimization": "memory_optimization",
            "Process Large Content": "process_large_content"
        }

        config_key = setting_map.get(sender.title)
        if config_key and set_config_value('performance', config_key, sender.state):
            rumps.notification("Clipboard Monitor", "Performance Setting",
                              f"{sender.title} is now {'enabled' if sender.state else 'disabled'}")
            self.restart_service(None)
        else:
            rumps.notification("Error", "Failed to update performance setting", "Could not save configuration")

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
                    # print(f"DEBUG: Exception in clear_clipboard_history's inner try: {type(file_error).__name__}: {file_error}") # Optional debug print
                    rumps.notification("Error", "Failed to clear history", f"Could not clear history file: {str(file_error)}")
                    # Removed temporary re-raise, as the issue is likely that this block isn't hit as expected.

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
