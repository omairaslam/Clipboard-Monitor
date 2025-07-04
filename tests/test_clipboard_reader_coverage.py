import unittest
from unittest.mock import patch
from clipboard_reader import ClipboardReader
from utils import ContentTracker

class TestClipboardReaderCoverage(unittest.TestCase):
    @patch('clipboard_reader.get_clipboard_content', return_value="dup")
    def test_tracker_false_branch(self, mock_get_clip):
        tracker = ContentTracker()
        reader = ClipboardReader(tracker)
        # First call, new content
        self.assertTrue(reader.has_content_changed("dup"))
        # Second call, duplicate content triggers return False (line 55)
        self.assertFalse(reader.has_content_changed("dup"))

    @patch('clipboard_reader.get_clipboard_content', return_value="unchanged")
    def test_get_content_if_changed_none_branch(self, mock_get_clip):
        reader = ClipboardReader()
        # First call sets baseline
        self.assertEqual(reader.get_content_if_changed(), "unchanged")
        # Second call returns None (line 78)
        self.assertIsNone(reader.get_content_if_changed())

if __name__ == '__main__':
    unittest.main()
