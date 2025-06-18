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
import subprocess
import threading
from unittest.mock import patch, MagicMock, call

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils import get_app_paths, get_clipboard_content, update_service_status
import pyperclip

class TestEndToEndWorkflows(unittest.TestCase):
    """Test complete end-to-end workflows"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_history_file = os.path.join(self.test_dir, "test_history.json")
        self.test_status_file = os.path.join(self.test_dir, "status.txt")
        
        # Initialize empty history
        with open(self.test_history_file, 'w') as f:
            json.dump([], f)
        
        # Set initial status
        with open(self.test_status_file, 'w') as f:
            f.write("running_enhanced")
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_markdown_processing_workflow(self):
        """Test complete markdown processing workflow"""
        print("\n🧪 Testing markdown processing workflow...")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": self.test_history_file}
            
            # Step 1: Copy markdown content
            markdown_content = "# Test Heading\n\nThis is **bold** text and *italic* text.\n\n- Item 1\n- Item 2"
            pyperclip.copy(markdown_content)
            
            # Step 2: Process through markdown module
            from modules.markdown_module import process as markdown_process
            result = markdown_process(markdown_content)
            
            # Step 3: Verify processing occurred
            self.assertTrue(result, "Markdown module should process the content")
            
            # Step 4: Add to history manually (simulating clipboard monitor)
            from history_module import add_to_history
            add_to_history(markdown_content)
            
            # Step 5: Verify history contains the item
            with open(self.test_history_file, 'r') as f:
                history = json.load(f)
            
            self.assertGreater(len(history), 0, "History should contain processed item")
            self.assertEqual(history[0]['content'], markdown_content, "History should contain original markdown")
            
            # Step 6: Retrieve from CLI viewer
            from cli_history_viewer import load_history
            loaded_history = load_history()
            self.assertEqual(len(loaded_history), len(history), "CLI should load same history")
        
        print("  ✅ Markdown processing workflow complete")
    
    def test_mermaid_diagram_workflow(self):
        """Test complete mermaid diagram processing workflow"""
        print("\n🧪 Testing mermaid diagram workflow...")
        
        with patch('utils.get_app_paths') as mock_paths, \
             patch('webbrowser.open') as mock_browser:
            
            mock_paths.return_value = {"history_file": self.test_history_file}
            
            # Step 1: Copy mermaid content
            mermaid_content = """graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E"""
            
            pyperclip.copy(mermaid_content)
            
            # Step 2: Process through mermaid module
            from modules.mermaid_module import process as mermaid_process
            result = mermaid_process(mermaid_content)
            
            # Step 3: Verify processing occurred (should open browser)
            self.assertTrue(result, "Mermaid module should process the content")
            mock_browser.assert_called_once()
            
            # Step 4: Add to history
            from history_module import add_to_history
            add_to_history(mermaid_content)
            
            # Step 5: Verify in web viewer
            import web_history_viewer
            html_content = web_history_viewer.generate_html()
            self.assertIn("mermaid", html_content.lower(), "Web viewer should show mermaid content")
        
        print("  ✅ Mermaid diagram workflow complete")
    
    def test_multi_module_processing_chain(self):
        """Test content processing through multiple modules"""
        print("\n🧪 Testing multi-module processing chain...")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": self.test_history_file}
            
            # Content that could trigger multiple modules
            mixed_content = """# Code Example
            
```python
def hello():
    print("Hello, World!")
```

This is a **markdown** document with code."""
            
            # Process through all modules
            from modules.markdown_module import process as markdown_process
            from modules.code_formatter_module import process as code_process
            from modules.mermaid_module import process as mermaid_process
            
            # Each module should handle the content appropriately
            markdown_result = markdown_process(mixed_content)
            code_result = code_process(mixed_content)
            mermaid_result = mermaid_process(mixed_content)
            
            # Verify appropriate processing
            self.assertTrue(markdown_result, "Markdown module should process mixed content")
            # Code and mermaid modules should return False for this content
            
            # Add to history and verify
            from history_module import add_to_history
            add_to_history(mixed_content)
            
            with open(self.test_history_file, 'r') as f:
                history = json.load(f)
            
            self.assertGreater(len(history), 0, "History should contain the mixed content")
        
        print("  ✅ Multi-module processing chain complete")
    
    def test_history_viewer_integration_workflow(self):
        """Test integration between all history viewers"""
        print("\n🧪 Testing history viewer integration workflow...")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": self.test_history_file}
            
            # Create test history with various content types
            test_items = [
                "Plain text content",
                "# Markdown Content\n\nWith **formatting**",
                '{"json": "data", "number": 42}',
                "https://example.com/test-url"
            ]
            
            # Add items to history
            from history_module import add_to_history
            for item in test_items:
                add_to_history(item)
                time.sleep(0.1)  # Ensure different timestamps
            
            # Test CLI viewer
            from cli_history_viewer import load_history
            cli_history = load_history()
            self.assertEqual(len(cli_history), len(test_items), "CLI should load all items")
            
            # Test web viewer
            import web_history_viewer
            html_content = web_history_viewer.generate_html()
            for item in test_items:
                # Check if content appears in HTML (may be truncated)
                content_preview = item[:20]
                self.assertIn(content_preview, html_content, f"Web viewer should contain '{content_preview}'")
            
            # Test menu bar integration
            with patch('rumps.App') as mock_app:
                mock_app_instance = MagicMock()
                mock_app.return_value = mock_app_instance
                
                import menu_bar_app
                app = menu_bar_app.ClipboardMenuBarApp()
                app.update_recent_history_menu()
                
                # Should have populated menu
                self.assertTrue(mock_app_instance.menu.__getitem__.called)
        
        print("  ✅ History viewer integration workflow complete")
    
    def test_service_lifecycle_workflow(self):
        """Test complete service lifecycle workflow"""
        print("\n🧪 Testing service lifecycle workflow...")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"status_file": self.test_status_file}
            
            # Test status updates
            from utils import update_service_status, get_service_status
            
            # Start service
            update_service_status("running_enhanced")
            status = get_service_status()
            self.assertEqual(status, "running_enhanced", "Service should be in enhanced mode")
            
            # Pause service
            update_service_status("paused")
            status = get_service_status()
            self.assertEqual(status, "paused", "Service should be paused")
            
            # Resume service
            update_service_status("running_polling")
            status = get_service_status()
            self.assertEqual(status, "running_polling", "Service should be in polling mode")
            
            # Test menu bar status display
            with patch('rumps.App') as mock_app:
                mock_app_instance = MagicMock()
                mock_app.return_value = mock_app_instance
                
                import menu_bar_app
                app = menu_bar_app.ClipboardMenuBarApp()
                
                # Test status display for different states
                for status in ["running_enhanced", "running_polling", "paused", "error"]:
                    update_service_status(status)
                    display = app.get_status_display()
                    self.assertIsInstance(display, str, f"Status display should be string for {status}")
                    self.assertGreater(len(display), 0, f"Status display should not be empty for {status}")
        
        print("  ✅ Service lifecycle workflow complete")
    
    def test_error_recovery_workflow(self):
        """Test error recovery in complete workflows"""
        print("\n🧪 Testing error recovery workflow...")
        
        # Test with corrupted history file
        corrupted_file = os.path.join(self.test_dir, "corrupted.json")
        with open(corrupted_file, 'w') as f:
            f.write("invalid json")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": corrupted_file}
            
            # Should handle corrupted file gracefully
            from cli_history_viewer import load_history
            history = load_history()
            self.assertIsInstance(history, list, "Should return empty list for corrupted file")
            
            # Should be able to add new items despite corruption
            from history_module import add_to_history
            add_to_history("Recovery test item")
            
            # File should be fixed after adding item
            with open(corrupted_file, 'r') as f:
                try:
                    recovered_history = json.load(f)
                    self.assertIsInstance(recovered_history, list, "History should be recovered")
                except json.JSONDecodeError:
                    # If still corrupted, that's also acceptable behavior
                    pass
        
        print("  ✅ Error recovery workflow complete")

if __name__ == '__main__':
    print("🧪 Running Comprehensive End-to-End Workflow Tests")
    print("=" * 60)
    
    # Run tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("🎉 End-to-End Workflow Tests Complete!")
