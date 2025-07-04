"""
Test cases for the Draw.io module.
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock pyperclip before it's imported by the module
sys.modules['pyperclip'] = MagicMock()

from modules.drawio_module import is_drawio_xml, encode_drawio_url, process

VALID_DRAWIO_XML = '''<mxfile><diagram><mxGraphModel><root><mxCell id="0"/><mxCell id="1" vertex="1"><mxGeometry/></mxCell></root></mxGraphModel></diagram></mxfile>'''
INVALID_XML = "<root><notdrawio/></root>"
MALFORMED_XML = "<mxfile><diagram></mxfile>"

class TestDrawioModule(unittest.TestCase):

    def test_is_drawio_xml_valid(self):
        self.assertTrue(is_drawio_xml(VALID_DRAWIO_XML))

    def test_is_drawio_xml_invalid(self):
        self.assertFalse(is_drawio_xml(INVALID_XML))

    def test_is_drawio_xml_malformed(self):
        self.assertFalse(is_drawio_xml(MALFORMED_XML))

    def test_is_drawio_xml_empty_string(self):
        self.assertFalse(is_drawio_xml(""))

    def test_is_drawio_xml_not_a_string(self):
        self.assertFalse(is_drawio_xml(None))
        self.assertFalse(is_drawio_xml(123))

    def test_encode_drawio_url(self):
        encoded = encode_drawio_url(VALID_DRAWIO_XML)
        self.assertIsInstance(encoded, str)
        self.assertGreater(len(encoded), 0)

    @patch('modules.drawio_module.webbrowser')
    @patch('modules.drawio_module.pyperclip')
    @patch('modules.drawio_module.show_notification')
    @patch('modules.drawio_module.ConfigManager')
    def test_process_clipboard_success_copy_and_open(self, mock_config_manager, mock_show_notification, mock_pyperclip, mock_webbrowser):
        mock_config = {
            "drawio_module": True,
            "drawio_copy_url": True,
            "drawio_open_in_browser": True
        }
        mock_config_manager.return_value.get_section.return_value = mock_config

        result = process(VALID_DRAWIO_XML)

        self.assertTrue(result)
        mock_pyperclip.copy.assert_called_once()
        mock_webbrowser.open_new.assert_called_once()
        mock_show_notification.assert_called_once()

    @patch('modules.drawio_module.webbrowser')
    @patch('modules.drawio_module.pyperclip')
    @patch('modules.drawio_module.show_notification')
    @patch('modules.drawio_module.ConfigManager')
    def test_process_clipboard_success_copy_only(self, mock_config_manager, mock_show_notification, mock_pyperclip, mock_webbrowser):
        mock_config = {
            "drawio_module": True,
            "drawio_copy_url": True,
            "drawio_open_in_browser": False
        }
        mock_config_manager.return_value.get_section.return_value = mock_config

        result = process(VALID_DRAWIO_XML)

        self.assertTrue(result)
        mock_pyperclip.copy.assert_called_once()
        mock_webbrowser.open_new.assert_not_called()
        mock_show_notification.assert_called_once()

    @patch('modules.drawio_module.webbrowser')
    @patch('modules.drawio_module.pyperclip')
    @patch('modules.drawio_module.show_notification')
    @patch('modules.drawio_module.ConfigManager')
    def test_process_clipboard_success_open_only(self, mock_config_manager, mock_show_notification, mock_pyperclip, mock_webbrowser):
        mock_config = {
            "drawio_module": True,
            "drawio_copy_url": False,
            "drawio_open_in_browser": True
        }
        mock_config_manager.return_value.get_section.return_value = mock_config

        result = process(VALID_DRAWIO_XML)

        self.assertTrue(result)
        mock_pyperclip.copy.assert_not_called()
        mock_webbrowser.open_new.assert_called_once()
        mock_show_notification.assert_called_once()

    @patch('modules.drawio_module.webbrowser')
    @patch('modules.drawio_module.pyperclip')
    @patch('modules.drawio_module.show_notification')
    @patch('modules.drawio_module.ConfigManager')
    def test_process_clipboard_disabled(self, mock_config_manager, mock_show_notification, mock_pyperclip, mock_webbrowser):
        mock_config = {"drawio_module": False}
        mock_config_manager.return_value.get_section.return_value = mock_config

        result = process(VALID_DRAWIO_XML)

        self.assertFalse(result)
        mock_pyperclip.copy.assert_not_called()
        mock_webbrowser.open_new.assert_not_called()
        mock_show_notification.assert_not_called()

    def test_process_clipboard_not_drawio(self):
        result = process(INVALID_XML)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
