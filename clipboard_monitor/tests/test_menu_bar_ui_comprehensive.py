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
from unittest.mock import patch, MagicMock, PropertyMock, call
import threading

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils import get_app_paths, update_service_status, get_service_status

class TestMenuBarUI(unittest.TestCase):
    """Test menu bar UI functionality and interactions"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test history
        self.test_history_file = os.path.join(self.test_dir, "test_history.json")
        self.test_history = [
            {"content": "Test item 1", "timestamp": time.time() - 100},
            {"content": "Test item 2", "timestamp": time.time() - 50},
            {"content": "# Markdown Test\n\nThis is **bold**", "timestamp": time.time() - 10}
        ]
        
        with open(self.test_history_file, 'w') as f:
            json.dump(self.test_history, f)
        
        # Create test status file
        self.test_status_file = os.path.join(self.test_dir, "status.txt")
        with open(self.test_status_file, 'w') as f:
            f.write("running_enhanced")
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('rumps.App')
    def test_menu_bar_initialization(self, mock_app):
        """Test menu bar app initialization"""
        print("\n🧪 Testing menu bar initialization...")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {
                "history_file": self.test_history_file,
                "status_file": self.test_status_file
            }
            
            import menu_bar_app
            app = menu_bar_app.ClipboardMenuBarApp()
            
            # Verify app was created with correct title
            mock_app.assert_called_once()
            init_call = mock_app.call_args
            self.assertIn("📋", init_call[0][0])  # Should have clipboard icon
            
        print("  ✅ Menu bar app initializes correctly")
    
    @patch('rumps.App')
    def test_menu_structure_creation(self, mock_app):
        """Test that menu structure is created correctly"""
        print("\n🧪 Testing menu structure creation...")
        
        mock_app_instance = MagicMock()
        mock_app.return_value = mock_app_instance
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {
                "history_file": self.test_history_file,
                "status_file": self.test_status_file
            }
            
            import menu_bar_app
            app = menu_bar_app.ClipboardMenuBarApp()
            
            # Verify menu items were added
            self.assertTrue(mock_app_instance.menu.__setitem__.called)
            
            # Check that key menu items exist
            menu_calls = [call[0][0] for call in mock_app_instance.menu.__setitem__.call_args_list]
            expected_items = ["Service Status", "Recent Clipboard Items", "View Clipboard History"]
            
            for item in expected_items:
                self.assertIn(item, menu_calls, f"Menu should contain '{item}'")
        
        print("  ✅ Menu structure created correctly")
    
    def test_service_status_display(self):
        """Test service status display and updates"""
        print("\n🧪 Testing service status display...")
        
        with patch('utils.get_app_paths') as mock_paths, \
             patch('rumps.App') as mock_app:
            
            mock_paths.return_value = {"status_file": self.test_status_file}
            mock_app_instance = MagicMock()
            mock_app.return_value = mock_app_instance
            
            import menu_bar_app
            app = menu_bar_app.ClipboardMenuBarApp()
            
            # Test different status values
            test_statuses = [
                ("running_enhanced", "🟢 Enhanced Mode"),
                ("running_polling", "🟡 Polling Mode"),
                ("paused", "⏸️ Paused"),
                ("error", "🔴 Error"),
                ("unknown", "❓ Unknown")
            ]
            
            for status, expected_display in test_statuses:
                with open(self.test_status_file, 'w') as f:
                    f.write(status)
                
                display = app.get_status_display()
                self.assertIn(expected_display, display, f"Status '{status}' should display '{expected_display}'")
        
        print("  ✅ Service status display works correctly")
    
    def test_recent_history_menu_population(self):
        """Test recent history menu population"""
        print("\n🧪 Testing recent history menu population...")
        
        with patch('utils.get_app_paths') as mock_paths, \
             patch('rumps.App') as mock_app:
            
            mock_paths.return_value = {"history_file": self.test_history_file}
            mock_app_instance = MagicMock()
            mock_app.return_value = mock_app_instance
            
            import menu_bar_app
            app = menu_bar_app.ClipboardMenuBarApp()
            
            # Test menu population
            app.update_recent_history_menu()
            
            # Verify menu was populated (should have clear and add operations)
            self.assertTrue(mock_app_instance.menu.__getitem__.called)
        
        print("  ✅ Recent history menu populates correctly")
    
    def test_menu_item_callbacks(self):
        """Test menu item callback functionality"""
        print("\n🧪 Testing menu item callbacks...")
        
        with patch('utils.get_app_paths') as mock_paths, \
             patch('rumps.App') as mock_app, \
             patch('subprocess.Popen') as mock_popen:
            
            mock_paths.return_value = {
                "history_file": self.test_history_file,
                "status_file": self.test_status_file
            }
            mock_app_instance = MagicMock()
            mock_app.return_value = mock_app_instance
            
            import menu_bar_app
            app = menu_bar_app.ClipboardMenuBarApp()
            
            # Test GUI viewer callback
            app.open_gui_viewer(None)
            mock_popen.assert_called()
            
            # Test web viewer callback
            app.open_web_viewer(None)
            self.assertEqual(mock_popen.call_count, 2)
            
            # Test CLI viewer callback
            app.open_cli_viewer(None)
            self.assertEqual(mock_popen.call_count, 3)
        
        print("  ✅ Menu item callbacks work correctly")
    
    def test_clipboard_item_copy_functionality(self):
        """Test copying items from history menu"""
        print("\n🧪 Testing clipboard item copy functionality...")
        
        with patch('utils.get_app_paths') as mock_paths, \
             patch('rumps.App') as mock_app, \
             patch('pyperclip.copy') as mock_copy:
            
            mock_paths.return_value = {"history_file": self.test_history_file}
            mock_app_instance = MagicMock()
            mock_app.return_value = mock_app_instance
            
            import menu_bar_app
            app = menu_bar_app.ClipboardMenuBarApp()
            
            # Test copying first item
            app.copy_to_clipboard("Test item 1")
            mock_copy.assert_called_with("Test item 1")
        
        print("  ✅ Clipboard item copy functionality works")
    
    def test_menu_refresh_functionality(self):
        """Test menu refresh functionality"""
        print("\n🧪 Testing menu refresh functionality...")
        
        with patch('utils.get_app_paths') as mock_paths, \
             patch('rumps.App') as mock_app:
            
            mock_paths.return_value = {"history_file": self.test_history_file}
            mock_app_instance = MagicMock()
            mock_app.return_value = mock_app_instance
            
            import menu_bar_app
            app = menu_bar_app.ClipboardMenuBarApp()
            
            # Test refresh functionality
            app.refresh_history_menu(None)
            
            # Should trigger menu update
            self.assertTrue(mock_app_instance.menu.__getitem__.called)
        
        print("  ✅ Menu refresh functionality works")
    
    def test_error_handling_in_ui(self):
        """Test error handling in UI operations"""
        print("\n🧪 Testing UI error handling...")
        
        # Test with corrupted history file
        corrupted_file = os.path.join(self.test_dir, "corrupted.json")
        with open(corrupted_file, 'w') as f:
            f.write("invalid json content")
        
        with patch('utils.get_app_paths') as mock_paths, \
             patch('rumps.App') as mock_app:
            
            mock_paths.return_value = {"history_file": corrupted_file}
            mock_app_instance = MagicMock()
            mock_app.return_value = mock_app_instance
            
            import menu_bar_app
            app = menu_bar_app.ClipboardMenuBarApp()
            
            # Should handle corrupted file gracefully
            app.update_recent_history_menu()
            
            # Should not crash
            self.assertTrue(True, "App handles corrupted history file")
        
        print("  ✅ UI error handling works correctly")

if __name__ == '__main__':
    print("🧪 Running Comprehensive Menu Bar UI Tests")
    print("=" * 60)
    
    # Run tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("🎉 Menu Bar UI Tests Complete!")
