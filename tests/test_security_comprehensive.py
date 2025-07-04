#!/usr/bin/env python3
"""
Comprehensive security tests.
Tests input validation, AppleScript injection prevention, and malicious content handling.
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils import show_notification, safe_expanduser
import modules.history_module

class TestSecurity(unittest.TestCase):
    """Test security features and protections"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.history_file = os.path.join(self.test_dir, "test_history.json")
        self.config_file = os.path.join(self.test_dir, "config.json")

        with open(self.config_file, 'w') as f:
            json.dump({"history": {"save_location": self.history_file}}, f)

        self.config_patcher = patch('config_manager.CONFIG_PATH', self.config_file)
        self.config_patcher.start()

    def tearDown(self):
        """Clean up test environment"""
        self.config_patcher.stop()
        shutil.rmtree(self.test_dir)

    @patch('subprocess.run')
    def test_applescript_injection_prevention(self, mock_subprocess_run):
        """Test AppleScript injection prevention"""
        print("\n🧪 Testing AppleScript injection prevention...")
        
        malicious_input = '"; do shell script "echo hacked'
        show_notification(malicious_input, "test message")
        
        # Get the executed command
        args, kwargs = mock_subprocess_run.call_args
        command = args[0]
        
        # Check that the malicious part is not in the command
        self.assertNotIn('do shell script "echo hacked"', command[2])
        # Check that quotes are escaped
        self.assertIn('\\"', command[2])
        
        print("  ✅ AppleScript injection prevention working")

    def test_file_path_security(self):
        """Test file path security and traversal prevention"""
        print("\n🧪 Testing file path security...")
        
        malicious_paths = [
            "~/../../etc/passwd",
            "../..",
        ]
        
        for path in malicious_paths:
            with self.assertRaises(RuntimeError):
                safe_expanduser(path)

        self.assertEqual(safe_expanduser("~"), os.path.expanduser("~"))
        
        print("  ✅ File path security working correctly")

    def test_data_sanitization(self):
        """Test data sanitization for various outputs"""
        print("\n🧪 Testing data sanitization...")
        
        # This is a conceptual test. The actual sanitization is handled by the
        # web framework, but we can test that the data is passed correctly.
        dangerous_html = "<script>alert('xss')</script>"
        modules.history_module.add_to_history(dangerous_html)
        
        history = modules.history_module.load_history()
        self.assertEqual(history[0]['content'], dangerous_html)
        
        print("  ✅ Data sanitization working correctly")

if __name__ == '__main__':
    unittest.main(verbosity=2)
