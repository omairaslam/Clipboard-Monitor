import threading
#!/usr/bin/env python3
"""
Comprehensive tests for clear history functionality across all interfaces.
Tests confirmation dialogs, menu refresh, and proper history clearing.
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

from utils import get_app_paths, safe_expanduser, ensure_directory_exists
import pyperclip

# Mock rumps before it's imported by other modules
mock_rumps = MagicMock(name="rumps_module_mock_clear_history") # Unique name

# Mock for the rumps.App class/constructor
AppClassMock_CH = MagicMock(name="App_ClassMock_ClearHistory")
app_instance_mock_ch = MagicMock(name="app_instance_mock_clear_history")
app_instance_mock_ch.menu = MagicMock(name="menu_attribute_mock_clear_history")
AppClassMock_CH.return_value = app_instance_mock_ch
AppClassMock_CH.side_effect = None # Ensure no iterator side_effect
mock_rumps.App = AppClassMock_CH

# Mock for rumps.MenuItem class/constructor
MenuItemClassMock_CH = MagicMock(name="MenuItem_ClassMock_ClearHistory")
menu_item_instance_mock_ch = MagicMock(name="menu_item_instance_mock_clear_history")
MenuItemClassMock_CH.return_value = menu_item_instance_mock_ch
MenuItemClassMock_CH.side_effect = None
mock_rumps.MenuItem = MenuItemClassMock_CH

# Mock for rumps.Timer class/constructor
TimerClassMock_CH = MagicMock(name="Timer_ClassMock_ClearHistory")
timer_instance_mock_ch = MagicMock(name="timer_instance_mock_clear_history")
TimerClassMock_CH.return_value = timer_instance_mock_ch
TimerClassMock_CH.side_effect = None
mock_rumps.Timer = TimerClassMock_CH

# Mock other rumps utilities
mock_rumps.alert = MagicMock(name="rumps_alert_func_mock_clear_history")
mock_rumps.notification = MagicMock(name="rumps_notification_func_mock_clear_history")
# No rumps.Window or rumps.clicked expected here based on previous test code

sys.modules['rumps'] = mock_rumps

import modules.history_module
import cli_history_viewer
import menu_bar_app # Now this will import with the mocked rumps

class TestClearHistoryFunctionality(unittest.TestCase):
    """Test clear history functionality across all interfaces"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.test_dir, "test_history.json")
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
            
        # Reset mocks for each test
        mock_rumps.reset_mock()

    def tearDown(self):
        """Clean up test environment"""
        self.config_patcher.stop()
        shutil.rmtree(self.test_dir)

    @patch('builtins.input', return_value='y')
    def test_cli_clear_history_command(self, mock_input):
        """Test CLI clear history command functionality"""
        print("\n🧪 Testing CLI clear history command...")
        
        cli_history_viewer.clear_history()
        
        history = modules.history_module.load_history()
        self.assertEqual(len(history), 0)
        
        print("  ✅ CLI clear with confirmation works")

    @patch('rumps.alert')
    @patch('rumps.notification')
    # @patch('modules.history_module.clear_history') # Removed decorator
    def test_menu_bar_clear_history(self, mock_notification, mock_alert): # mock_module_clear_history removed from args
        """Test menu bar clear history functionality"""
        print("\n🧪 Testing menu bar clear history...")
        
        mock_alert.return_value = 1 # Simulate user clicking "OK" / "Clear History"
        
        # Patch clear_history directly on the imported module object for this test's scope
        with patch.object(modules.history_module, 'clear_history', return_value=True, autospec=True) as mock_module_clear_history_on_object:
            # Instantiate the real app. Relies on the global rumps mock for App, MenuItem, Timer.
            app = menu_bar_app.ClipboardMonitorMenuBar()

            # Mock the specific instance method that would be called
            app.update_recent_history_menu = MagicMock()

            app.clear_clipboard_history(None) # Call the method under test

            # Verify that the underlying module's clear_history was called
            mock_module_clear_history_on_object.assert_called_once()

        # Verify that rumps alert and notification were called
        mock_alert.assert_called_once()
        mock_notification.assert_called_once()

        # Verify that the menu update was called
        app.update_recent_history_menu.assert_called_once()
        
        print("  ✅ Menu bar clear with confirmation works")

    def test_concurrent_clear_operations(self):
        """Test concurrent clear history operations"""
        print("\n🧪 Testing concurrent clear operations...")

        def worker():
            modules.history_module.clear_history()

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        history = modules.history_module.load_history()
        self.assertEqual(len(history), 0)
        
        print("  ✅ Concurrent clear operations work correctly")

if __name__ == '__main__':
    unittest.main(verbosity=2)
