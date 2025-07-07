#!/usr/bin/env python3
"""
Comprehensive tests for menu bar UI functionality.
Tests menu interactions, state changes, icon updates, and UI responsiveness.
"""

import os
import sys
import json
import time
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Create a fully configured mock for the 'rumps' module
mock_rumps_module = MagicMock(name="rumps_module_mock_ui")

# Configure rumps.App (the class/constructor mock)
AppClassMock_UI = MagicMock(name="App_ClassMock_UI")
app_instance_mock_ui = MagicMock(name="app_instance_mock_ui")
app_instance_mock_ui.menu = MagicMock(name="menu_attribute_mock_ui")
AppClassMock_UI.return_value = app_instance_mock_ui
AppClassMock_UI.side_effect = None
mock_rumps_module.App = AppClassMock_UI

# Configure rumps.MenuItem (the class/constructor mock)
MenuItemClassMock_UI = MagicMock(name="MenuItem_ClassMock_UI")
menu_item_instance_mock_ui = MagicMock(name="menu_item_instance_mock_ui")
menu_item_instance_mock_ui.add = MagicMock(name="menuitem_add_method_mock")
menu_item_instance_mock_ui.set_callback = MagicMock(name="menuitem_set_callback_mock")
# Add other attributes like .title, .state as MagicMocks if they are set/get in __init__
menu_item_instance_mock_ui.title = None # Or MagicMock() if it's accessed
menu_item_instance_mock_ui.state = False # Or MagicMock()
MenuItemClassMock_UI.return_value = menu_item_instance_mock_ui
MenuItemClassMock_UI.side_effect = None
mock_rumps_module.MenuItem = MenuItemClassMock_UI

# Configure rumps.Timer (the class/constructor mock)
TimerClassMock_UI = MagicMock(name="Timer_ClassMock_UI")
timer_instance_mock_ui = MagicMock(name="timer_instance_mock_ui")
timer_instance_mock_ui.start = MagicMock(name="timer_start_method_mock_ui")
TimerClassMock_UI.return_value = timer_instance_mock_ui
TimerClassMock_UI.side_effect = None
mock_rumps_module.Timer = TimerClassMock_UI

# Mock other rumps functions/classes if menu_bar_app.py calls them directly from rumps module
mock_rumps_module.alert = MagicMock(name="global_rumps_alert_mock_ui")
mock_rumps_module.notification = MagicMock(name="global_rumps_notification_mock_ui")
WindowConstructorMock_UI = MagicMock(name="Window_ClassMock_UI")
window_instance_mock_ui = MagicMock(name="window_instance_mock_ui")
window_instance_mock_ui.run = MagicMock(name="window_run_method_mock_ui")
WindowConstructorMock_UI.return_value = window_instance_mock_ui
WindowConstructorMock_UI.side_effect = None
mock_rumps_module.Window = WindowConstructorMock_UI
mock_rumps_module.separator = None # rumps.separator is often None or a specific string/object
                                 # If it's a callable that returns a separator, mock that.
                                 # For now, assume it's an attribute.

# Apply the mock to sys.modules BEFORE menu_bar_app is imported
sys.modules['rumps'] = mock_rumps_module

import menu_bar_app # This will now import the mock_rumps_module as 'rumps'

class TestMenuBarUI(unittest.TestCase):
    """Test menu bar UI functionality and interactions"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.test_dir, "test_history.json")
        self.status_file = os.path.join(self.test_dir, "status.txt")
        self.config_file = os.path.join(self.test_dir, "config.json")

        # Create a config file that points to the test history file
        with open(self.config_file, 'w') as f:
            json.dump({"history": {"save_location": self.history_file}}, f)

        self.config_patcher = patch('config_manager.CONFIG_PATH', self.config_file)
        self.config_patcher.start()

        # Write initial history
        self.test_history = [
            {"content": "Test item 1", "timestamp": time.time() - 100},
            {"content": "Test item 2", "timestamp": time.time() - 50},
        ]
        with open(self.history_file, 'w') as f:
            json.dump(self.test_history, f)
            
        # Write initial status
        with open(self.status_file, 'w') as f:
            f.write("running_enhanced")

        # Reset mocks for each test
        mock_rumps_module.reset_mock()

    def tearDown(self):
        """Clean up test environment"""
        self.config_patcher.stop()
        shutil.rmtree(self.test_dir)

    @patch.object(menu_bar_app.rumps, 'MenuItem')
    @patch.object(menu_bar_app.rumps, 'Timer')
    def test_menu_bar_initialization(self, MockRumpsTimer, MockRumpsMenuItem): # Removed MockRumpsAppInit
        """Test menu bar app initialization"""
        print("\n🧪 Testing menu bar initialization...")

        # Ensure the global mock for rumps.App is correctly configured for this call
        mock_rumps_module.App.reset_mock() # Reset call count specifically for App class mock
        app_instance_mock = MagicMock(name="app_instance_for_init_test")
        app_instance_mock.menu = MagicMock(name="menu_for_init_test")
        mock_rumps_module.App.return_value = app_instance_mock
        mock_rumps_module.App.side_effect = None

        # Configure MenuItem and Timer mocks (their constructors are MockRumpsMenuItem, MockRumpsTimer)
        menu_item_instance = MagicMock(name="menu_item_instance_from_decorator")
        menu_item_instance.add = MagicMock()
        menu_item_instance.set_callback = MagicMock()
        MockRumpsMenuItem.return_value = menu_item_instance
        MockRumpsMenuItem.side_effect = None # Ensure constructor mock doesn't iterate

        timer_instance = MagicMock(name="timer_instance_from_decorator")
        timer_instance.start = MagicMock()
        MockRumpsTimer.return_value = timer_instance
        MockRumpsTimer.side_effect = None # Ensure constructor mock doesn't iterate
        
        app = menu_bar_app.ClipboardMonitorMenuBar()
        
        # Assert that the mocked rumps.App constructor (mock_rumps_module.App) was called
        mock_rumps_module.App.assert_called_once_with("📋", quit_button=None)

        self.assertTrue(MockRumpsMenuItem.called)
        self.assertTrue(MockRumpsTimer.called)
        timer_instance.start.assert_called()
        
        print("  ✅ Menu bar app initializes correctly")

    @patch('subprocess.Popen')
    # Apply similar patching for other tests instantiating ClipboardMonitorMenuBar
    @patch.object(menu_bar_app.rumps, 'MenuItem')
    @patch.object(menu_bar_app.rumps, 'Timer')
    # No patch for App.__init__ here, will rely on global mock mock_rumps_module.App
    def test_menu_item_callbacks(self, MockRumpsTimer, MockRumpsMenuItem, mock_popen): # MockRumpsAppInit removed
        """Test menu item callback functionality"""
        print("\n🧪 Testing menu item callbacks...")

        # Reset relevant global mocks
        mock_rumps_module.App.reset_mock() # Super init will be called
        mock_rumps_module.MenuItem.reset_mock()
        mock_rumps_module.Timer.reset_mock()

        app = menu_bar_app.ClipboardMonitorMenuBar()
        
        # Simulate clicking "View Clipboard History" -> open_web_history_viewer
        app.open_web_history_viewer(None)
        mock_popen.assert_called()
        
        print("  ✅ Menu item callbacks work correctly")

    @patch('pyperclip.copy')
    def test_clipboard_item_copy_functionality(self, mock_pyperclip_copy):
        """Test copying items from history menu"""
        print("\n🧪 Testing clipboard item copy functionality...")

        # Reset relevant global mocks
        mock_rumps_module.App.reset_mock()
        mock_rumps_module.MenuItem.reset_mock()
        mock_rumps_module.Timer.reset_mock()
        
        app = menu_bar_app.ClipboardMonitorMenuBar()
        
        app.copy_to_clipboard("test content")
        mock_pyperclip_copy.assert_called_once_with("test content")
        
        print("  ✅ Clipboard item copy functionality works")

if __name__ == '__main__':
    unittest.main(verbosity=2)
