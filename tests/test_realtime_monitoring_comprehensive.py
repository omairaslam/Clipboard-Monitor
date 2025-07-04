#!/usr/bin/env python3
"""
Comprehensive real-time monitoring tests.
Tests clipboard change detection, content deduplication, and monitoring modes.
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

import modules.history_module
from clipboard_reader import ClipboardReader
from utils import ContentTracker

class TestRealtimeMonitoring(unittest.TestCase):
    @patch('clipboard_reader.get_clipboard_content', return_value="dup")
    def test_has_content_changed_tracker_false_branch(self, mock_get_clip):
        """Test has_content_changed returns False for duplicate content (tracker branch, line 55)."""
        tracker = ContentTracker()
        reader = ClipboardReader(tracker)
        # First call, new content
        self.assertTrue(reader.has_content_changed("dup"))
        # Second call, duplicate content triggers return False (line 55)
        self.assertFalse(reader.has_content_changed("dup"))

    @patch('clipboard_reader.get_clipboard_content', return_value="unchanged")
    def test_get_content_if_changed_none_branch(self, mock_get_clip):
        """Test get_content_if_changed returns None if content is unchanged (line 78)."""
        reader = ClipboardReader()
        # First call sets baseline
        self.assertEqual(reader.get_content_if_changed(), "unchanged")
        # Second call returns None (line 78)
        self.assertIsNone(reader.get_content_if_changed())
    @patch('clipboard_reader.get_clipboard_content', return_value="unchanged content")
    def test_no_change_returns_none(self, mock_get_clip):
        """Test get_content_if_changed returns None if content is unchanged."""
        reader = ClipboardReader()
        # First call sets the baseline
        self.assertEqual(reader.get_content_if_changed(), "unchanged content")
        # Second call with same content should return None
        self.assertIsNone(reader.get_content_if_changed())

    @patch('clipboard_reader.get_clipboard_content', return_value="track me")
    def test_has_content_changed_with_tracker(self, mock_get_clip):
        """Test has_content_changed returns False for duplicate content with tracker."""
        tracker = ContentTracker()
        reader = ClipboardReader(tracker)
        # First call, new content
        self.assertTrue(reader.has_content_changed("track me"))
        # Second call, duplicate content
        self.assertFalse(reader.has_content_changed("track me"))

    def test_reset_tracking(self):
        """Test reset_tracking resets last_content and last_content_hash."""
        reader = ClipboardReader()
        reader.last_content = "something"
        reader.last_content_hash = "hash"
        reader.reset_tracking()
        self.assertIsNone(reader.last_content)
        self.assertIsNone(reader.last_content_hash)
    """Test real-time monitoring functionality"""

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

        modules.history_module.clear_history()
        # Reset the content tracker for each test
        modules.history_module.reset_content_tracker()

    def tearDown(self):
        """Clean up test environment"""
        self.config_patcher.stop()
        shutil.rmtree(self.test_dir)

    @patch('clipboard_reader.get_clipboard_content', return_value="initial content")
    def test_clipboard_change_detection(self, mock_get_clip):
        """Test that clipboard changes are detected."""
        print("\n🧪 Testing clipboard change detection...")

        reader = ClipboardReader(ContentTracker())
        
        # First read establishes baseline
        self.assertEqual(reader.get_changed_clipboard_content(), "initial content")
        
        # Second read with same content should return None
        self.assertIsNone(reader.get_changed_clipboard_content())
        
        # Change the clipboard content
        mock_get_clip.return_value = "new content"
        self.assertEqual(reader.get_changed_clipboard_content(), "new content")
        
        print("  ✅ Clipboard change detection works correctly")

    @patch('pyperclip.paste')
    def test_content_deduplication(self, mock_paste):
        """Test that duplicate content is not processed repeatedly."""
        print("\n🧪 Testing content deduplication...")

        tracker = ContentTracker()
        
        mock_paste.return_value = "duplicate content"
        
        # First time, should be processed
        self.assertFalse(tracker.has_processed("duplicate content"))
        tracker.add_content("duplicate content")
        
        # Second time, should be skipped
        self.assertTrue(tracker.has_processed("duplicate content"))
        
        print("  ✅ Content deduplication works correctly")

    @patch('clipboard_reader.get_clipboard_content', return_value="content while paused")
    def test_monitoring_pause_resume(self, mock_get_clip):
        """Test pausing and resuming clipboard monitoring."""
        print("\n🧪 Testing monitoring pause and resume...")

        reader = ClipboardReader(ContentTracker())
        
        # Pause monitoring
        reader.is_paused = True
        mock_get_clip.return_value = "content while paused"
        self.assertIsNone(reader.get_changed_clipboard_content())
        
        # Resume monitoring
        reader.is_paused = False
        self.assertEqual(reader.get_changed_clipboard_content(), "content while paused")
        
        print("  ✅ Monitoring pause and resume works correctly")

if __name__ == '__main__':
    unittest.main(verbosity=2)
