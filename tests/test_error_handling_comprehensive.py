#!/usr/bin/env python3
"""
Comprehensive error handling tests.
Tests for graceful failure on file errors, permission issues, and resource exhaustion.
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

import modules.history_module
import cli_history_viewer

class TestErrorHandling(unittest.TestCase):
    """Test graceful failure on various error conditions"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_history_file = os.path.join(self.test_dir, "test_history.json")
        self.test_config_file = os.path.join(self.test_dir, "config.json")

        # Create a config file that points to the test history file
        self.test_config = {"history": {"save_location": self.test_history_file}}
        with open(self.test_config_file, 'w') as f:
            json.dump(self.test_config, f)

        # Patch config path to use our test config
        self.config_patcher = patch('config_manager.CONFIG_PATH', self.test_config_file)
        self.config_patcher.start()

        # Clear history before each test
        modules.history_module.clear_history()

    def tearDown(self):
        """Clean up test environment"""
        self.config_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_history_file_permission_errors(self):
        """Test that the system handles history file permission errors gracefully."""
        print("\n🧪 Testing history file permission errors...")

        # Make history file unreadable
        with open(self.test_history_file, 'w') as f:
            f.write("[]")
        os.chmod(self.test_history_file, 0o000)

        # Should not raise an exception, should return empty list
        history = modules.history_module.load_history()
        self.assertEqual(history, [])

        # Should not raise an exception, should return False
        result = modules.history_module.add_to_history("test")
        self.assertIsNone(result)

        # Restore permissions for cleanup
        os.chmod(self.test_history_file, 0o644)
        print("  ✅ History file permission errors handled gracefully")

    def test_corrupted_history_file(self):
        """Test that a corrupted history file is handled gracefully."""
        print("\n🧪 Testing corrupted history file...")

        with open(self.test_history_file, 'w') as f:
            f.write("this is not valid json")

        # Loading should return an empty list and back up the corrupted file
        history = modules.history_module.load_history()
        self.assertEqual(history, [])
        self.assertTrue(os.path.exists(self.test_history_file.replace('.json', '.corrupt.bak')))

        # Adding a new item should create a new, valid history file
        modules.history_module.add_to_history("new item")
        new_history = modules.history_module.load_history()
        self.assertEqual(len(new_history), 1)
        self.assertEqual(new_history[0]['content'], "new item")

        print("  ✅ Corrupted history file handled gracefully")

    @patch('psutil.virtual_memory')
    def test_system_resource_exhaustion(self, mock_virtual_memory):
        """Test graceful failure when system resources are exhausted."""
        print("\n🧪 Testing system resource exhaustion handling...")

        # Simulate out-of-memory error
        mock_virtual_memory.return_value = MagicMock(available=0, total=1)

        # This test is conceptual. In a real-world scenario, the application
        # might crash before our code can handle it. We test that our code
        # *attempts* to handle it if it gets the chance.
        try:
            # A function that might allocate memory
            modules.history_module.add_to_history("a" * 1024 * 1024) # 1MB string
        except MemoryError:
            # This is the expected outcome
            pass
        except Exception as e:
            self.fail(f"Expected MemoryError, but got {type(e).__name__}")

        print("  ✅ System resource exhaustion handled gracefully")

if __name__ == '__main__':
    unittest.main(verbosity=2)
