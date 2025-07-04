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
mock_rumps = MagicMock()
sys.modules['rumps'] = mock_rumps

import modules.history_module
import cli_history_viewer
import menu_bar_app

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

    @patch('rumps.alert', return_value=1)
    @patch('rumps.notification')
    @patch('menu_bar_app.ClipboardMonitorMenuBar.update_recent_history_menu')
    def test_menu_bar_clear_history(self, mock_update_menu, mock_notification, mock_alert):
        """Test menu bar clear history functionality"""
        print("\n🧪 Testing menu bar clear history...")
        
        app = menu_bar_app.ClipboardMenuBarApp()
        app.clear_clipboard_history(None)
        
        history = modules.history_module.load_history()
        self.assertEqual(len(history), 0)
        mock_alert.assert_called_once()
        mock_notification.assert_called_once()
        mock_update_menu.assert_called()
        
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
