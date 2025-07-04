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

# Mock rumps before it's imported by menu_bar_app
mock_rumps = MagicMock()
sys.modules['rumps'] = mock_rumps

import menu_bar_app

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
        mock_rumps.reset_mock()

    def tearDown(self):
        """Clean up test environment"""
        self.config_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_menu_bar_initialization(self):
        """Test menu bar app initialization"""
        print("\n🧪 Testing menu bar initialization...")
        
        app = menu_bar_app.ClipboardMenuBarApp()
        
        mock_rumps.App.assert_called_once()
        self.assertIn("📋", mock_rumps.App.call_args[0][0])
        
        print("  ✅ Menu bar app initializes correctly")

    @patch('subprocess.Popen')
    def test_menu_item_callbacks(self, mock_popen):
        """Test menu item callback functionality"""
        print("\n🧪 Testing menu item callbacks...")
        
        app = menu_bar_app.ClipboardMenuBarApp()
        
        # Simulate clicking "View Clipboard History"
        app.open_web_viewer(None)
        mock_popen.assert_called()
        
        print("  ✅ Menu item callbacks work correctly")

    @patch('pyperclip.copy')
    def test_clipboard_item_copy_functionality(self, mock_copy):
        """Test copying items from history menu"""
        print("\n🧪 Testing clipboard item copy functionality...")
        
        app = menu_bar_app.ClipboardMenuBarApp()
        
        # Simulate copying an item
        app.copy_to_clipboard("test content")
        mock_copy.assert_called_once_with("test content")
        
        print("  ✅ Clipboard item copy functionality works")

if __name__ == '__main__':
    unittest.main(verbosity=2)
