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
import subprocess
import unittest
from unittest.mock import patch, MagicMock, call
import threading

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils import get_app_paths, safe_expanduser, ensure_directory_exists
import pyperclip

class TestClearHistoryFunctionality(unittest.TestCase):
    """Test clear history functionality across all interfaces"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_paths = get_app_paths()
        
        # Create test history file
        self.test_history_file = os.path.join(self.test_dir, "test_history.json")
        self.test_history = [
            {"content": "Test item 1", "timestamp": time.time() - 100},
            {"content": "Test item 2", "timestamp": time.time() - 50},
            {"content": "Test item 3", "timestamp": time.time() - 10}
        ]
        
        with open(self.test_history_file, 'w') as f:
            json.dump(self.test_history, f)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_cli_clear_history_command(self):
        """Test CLI clear history command functionality"""
        print("\n🧪 Testing CLI clear history command...")
        
        # Test with confirmation 'y'
        with patch('builtins.input', return_value='y'):
            with patch('utils.get_app_paths') as mock_paths:
                mock_paths.return_value = {"history_file": self.test_history_file}
                
                # Import and test CLI clear function
                from cli_history_viewer import clear_history
                clear_history()
                
                # Verify history was cleared
                with open(self.test_history_file, 'r') as f:
                    history = json.load(f)
                self.assertEqual(len(history), 0, "History should be empty after clearing")
        
        print("  ✅ CLI clear with confirmation works")
        
        # Reset history for next test
        with open(self.test_history_file, 'w') as f:
            json.dump(self.test_history, f)
        
        # Test with confirmation 'n'
        with patch('builtins.input', return_value='n'):
            with patch('utils.get_app_paths') as mock_paths:
                mock_paths.return_value = {"history_file": self.test_history_file}
                
                from cli_history_viewer import clear_history
                clear_history()
                
                # Verify history was NOT cleared
                with open(self.test_history_file, 'r') as f:
                    history = json.load(f)
                self.assertEqual(len(history), 3, "History should remain unchanged when cancelled")
        
        print("  ✅ CLI clear cancellation works")
    
    def test_menu_bar_clear_history(self):
        """Test menu bar clear history functionality"""
        print("\n🧪 Testing menu bar clear history...")
        
        # Mock rumps for testing
        with patch('rumps.alert') as mock_alert, \
             patch('rumps.notification') as mock_notification, \
             patch('utils.get_app_paths') as mock_paths:
            
            mock_paths.return_value = {"history_file": self.test_history_file}
            mock_alert.return_value = 1  # Simulate OK clicked
            
            # Import menu bar app
            import menu_bar_app
            
            # Create app instance
            app = menu_bar_app.ClipboardMenuBarApp()
            
            # Test clear history method
            app.clear_clipboard_history(None)
            
            # Verify alert was shown
            mock_alert.assert_called_once()
            alert_call = mock_alert.call_args
            self.assertIn("Clear Clipboard History", alert_call[1]['title'])
            self.assertIn("cannot be undone", alert_call[1]['message'])
            
            # Verify notification was shown
            mock_notification.assert_called_once()
            
            # Verify history was cleared
            with open(self.test_history_file, 'r') as f:
                history = json.load(f)
            self.assertEqual(len(history), 0, "History should be empty after menu bar clear")
        
        print("  ✅ Menu bar clear with confirmation works")
        
        # Test cancellation
        with open(self.test_history_file, 'w') as f:
            json.dump(self.test_history, f)
        
        with patch('rumps.alert') as mock_alert, \
             patch('utils.get_app_paths') as mock_paths:
            
            mock_paths.return_value = {"history_file": self.test_history_file}
            mock_alert.return_value = 0  # Simulate Cancel clicked
            
            app = menu_bar_app.ClipboardMenuBarApp()
            app.clear_clipboard_history(None)
            
            # Verify history was NOT cleared
            with open(self.test_history_file, 'r') as f:
                history = json.load(f)
            self.assertEqual(len(history), 3, "History should remain when cancelled")
        
        print("  ✅ Menu bar clear cancellation works")
    
    def test_history_file_error_handling(self):
        """Test error handling when history file operations fail"""
        print("\n🧪 Testing clear history error handling...")
        
        # Test with non-existent directory
        bad_path = "/nonexistent/directory/history.json"
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": bad_path}
            
            # Test CLI error handling
            with patch('builtins.input', return_value='y'):
                from cli_history_viewer import clear_history
                # Should not raise exception
                clear_history()
        
        print("  ✅ CLI handles file errors gracefully")
        
        # Test menu bar error handling
        with patch('rumps.alert') as mock_alert, \
             patch('utils.get_app_paths') as mock_paths:
            
            mock_paths.return_value = {"history_file": bad_path}
            mock_alert.return_value = 1
            
            app = menu_bar_app.ClipboardMenuBarApp()
            # Should not raise exception
            app.clear_clipboard_history(None)
        
        print("  ✅ Menu bar handles file errors gracefully")
    
    def test_concurrent_clear_operations(self):
        """Test concurrent clear history operations"""
        print("\n🧪 Testing concurrent clear operations...")
        
        # Create multiple history files
        history_files = []
        for i in range(3):
            path = os.path.join(self.test_dir, f"history_{i}.json")
            with open(path, 'w') as f:
                json.dump(self.test_history, f)
            history_files.append(path)
        
        def clear_history_worker(history_file):
            """Worker function to clear history"""
            with patch('utils.get_app_paths') as mock_paths:
                mock_paths.return_value = {"history_file": history_file}
                with patch('builtins.input', return_value='y'):
                    from cli_history_viewer import clear_history
                    clear_history()
        
        # Start concurrent clear operations
        threads = []
        for history_file in history_files:
            thread = threading.Thread(target=clear_history_worker, args=(history_file,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all histories were cleared
        for history_file in history_files:
            with open(history_file, 'r') as f:
                history = json.load(f)
            self.assertEqual(len(history), 0, f"History {history_file} should be cleared")
        
        print("  ✅ Concurrent clear operations work correctly")

if __name__ == '__main__':
    print("🧪 Running Comprehensive Clear History Tests")
    print("=" * 60)
    
    # Run tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("🎉 Clear History Tests Complete!")
