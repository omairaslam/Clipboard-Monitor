#!/usr/bin/env python3
"""
Comprehensive end-to-end workflow tests.
Tests complete workflows from clipboard copy to history retrieval across all interfaces.
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

from utils import get_clipboard_content, update_service_status, get_service_status
import pyperclip


# Robust mock for rumps: always returns a new MagicMock for any attribute
class RobustRumpsMock(MagicMock):
    def __getattr__(self, name):
        return MagicMock()

sys.modules['rumps'] = RobustRumpsMock()

import modules.history_module
import cli_history_viewer
import web_history_viewer
import menu_bar_app

class TestEndToEndWorkflows(unittest.TestCase):
    """Test complete end-to-end workflows"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_history_file = os.path.join(self.test_dir, "test_history.json")
        self.test_status_file = os.path.join(self.test_dir, "status.txt")
        self.test_config_file = os.path.join(self.test_dir, "config.json")

        # Create a config file that points to the test history file
        self.test_config = {
            "history": {"save_location": self.test_history_file},
            "modules": {
                "markdown_modify_clipboard": True,
                "code_formatter_read_only": True,
                "mermaid_auto_open": True
            }
        }
        with open(self.test_config_file, 'w') as f:
            json.dump(self.test_config, f)

        # Patch get_app_paths and config to be consistent
        self.get_app_paths_patcher = patch('utils.get_app_paths', return_value={
            "history_file": self.test_history_file,
            "status_file": self.test_status_file,
            "base_dir": self.test_dir
        })
        self.config_patcher = patch('config_manager.CONFIG_PATH', self.test_config_file)
        
        self.get_app_paths_patcher.start()
        self.config_patcher.start()

        # Reset history and mocks
        modules.history_module.clear_history()
        # No need to reset mock_rumps; RobustRumpsMock handles all calls

    def tearDown(self):
        """Clean up test environment"""
        self.config_patcher.stop()
        self.get_app_paths_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_full_workflow_with_history_viewers(self):
        """Test full workflow from copy to viewing in all viewers."""
        print("\n🧪 Testing full workflow with history viewers...")

        # 1. Add items to history
        test_items = ["item 1", "# markdown", "item 3"]
        for item in test_items:
            modules.history_module.add_to_history(item)
            time.sleep(0.01) # ensure distinct timestamps

        # 2. Verify with CLI viewer
        cli_history = cli_history_viewer.load_history()
        self.assertEqual(len(cli_history), len(test_items))
        self.assertEqual(cli_history[0]['content'], test_items[-1])

        # 3. Verify with Web viewer
        html_content = web_history_viewer.generate_html()
        for item in test_items:
            self.assertIn(item, html_content)

        # 4. Verify with Menu Bar viewer
        app = menu_bar_app.ClipboardMenuBarApp()
        app.update_recent_history_menu()
        recent_items_menu = app.menu["Recent Clipboard Items"]
        self.assertEqual(len(recent_items_menu.keys()), len(test_items) + 2) # + separator and clear
        self.assertIn("item 1", recent_items_menu)

        print("  ✅ Full workflow with history viewers complete")

    def test_service_lifecycle_workflow(self):
        """Test complete service lifecycle workflow"""
        print("\n🧪 Testing service lifecycle workflow...")
        
        # Test status updates
        update_service_status("running_enhanced")
        self.assertEqual(get_service_status(), "running_enhanced")
        
        update_service_status("paused")
        self.assertEqual(get_service_status(), "paused")

        # Test menu bar status display
        app = menu_bar_app.ClipboardMenuBarApp()
        app.update_status(None)
        self.assertEqual(app.menu["Service Status"].title, "Service Status: ⏸️ Paused")
        self.assertIn("⏸️", app.title)

        print("  ✅ Service lifecycle workflow complete")

    def test_error_recovery_workflow(self):
        """Test error recovery in complete workflows"""
        print("\n🧪 Testing error recovery workflow...")
        
        # Corrupt the history file
        with open(self.test_history_file, 'w') as f:
            f.write("invalid json")

        # CLI viewer should handle it gracefully
        self.assertEqual(cli_history_viewer.load_history(), [])

        # Adding a new item should recover the file
        modules.history_module.add_to_history("recovery item")
        
        recovered_history = cli_history_viewer.load_history()
        self.assertEqual(len(recovered_history), 1)
        self.assertEqual(recovered_history[0]['content'], "recovery item")

        print("  ✅ Error recovery workflow complete")

if __name__ == '__main__':
    unittest.main(verbosity=2)
