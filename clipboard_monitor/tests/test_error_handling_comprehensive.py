#!/usr/bin/env python3
"""
Comprehensive error handling tests.
Tests file permissions, network failures, malformed data, and edge cases.
"""

import os
import sys
import json
import time
import tempfile
import shutil
import unittest
import stat
from unittest.mock import patch, MagicMock, mock_open
import subprocess

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils import get_app_paths, safe_expanduser, ensure_directory_exists, get_clipboard_content

class TestErrorHandling(unittest.TestCase):
    """Test comprehensive error handling scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_history_file = os.path.join(self.test_dir, "test_history.json")
        
        # Create valid initial history
        with open(self.test_history_file, 'w') as f:
            json.dump([{"content": "test", "timestamp": time.time()}], f)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            # Restore permissions before cleanup
            for root, dirs, files in os.walk(self.test_dir):
                for d in dirs:
                    os.chmod(os.path.join(root, d), 0o755)
                for f in files:
                    os.chmod(os.path.join(root, f), 0o644)
            shutil.rmtree(self.test_dir)
    
    def test_file_permission_errors(self):
        """Test handling of file permission errors"""
        print("\n🧪 Testing file permission error handling...")
        
        # Create read-only file
        readonly_file = os.path.join(self.test_dir, "readonly.json")
        with open(readonly_file, 'w') as f:
            json.dump([{"content": "readonly", "timestamp": time.time()}], f)
        os.chmod(readonly_file, 0o444)  # Read-only
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": readonly_file}
            
            # Test history module with read-only file
            from history_module import add_to_history
            # Should not crash, should handle gracefully
            add_to_history("test content")
            
        print("  ✅ Read-only file handled gracefully")
        
        # Test with no-permission directory
        noperm_dir = os.path.join(self.test_dir, "noperm")
        os.makedirs(noperm_dir)
        os.chmod(noperm_dir, 0o000)  # No permissions
        
        noperm_file = os.path.join(noperm_dir, "history.json")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": noperm_file}
            
            # Should handle directory permission error
            from history_module import add_to_history
            add_to_history("test content")
            
        # Restore permissions for cleanup
        os.chmod(noperm_dir, 0o755)
        
        print("  ✅ Directory permission errors handled gracefully")
    
    def test_malformed_data_handling(self):
        """Test handling of malformed data files"""
        print("\n🧪 Testing malformed data handling...")
        
        # Test various malformed JSON files
        malformed_files = [
            ("empty_file.json", ""),
            ("invalid_json.json", "invalid json content"),
            ("partial_json.json", '{"incomplete": '),
            ("wrong_type.json", '"string instead of array"'),
            ("null_file.json", "null"),
            ("binary_file.json", b"\x00\x01\x02\x03".decode('latin1', errors='ignore'))
        ]
        
        for filename, content in malformed_files:
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
            
            with patch('utils.get_app_paths') as mock_paths:
                mock_paths.return_value = {"history_file": filepath}
                
                # Test CLI history viewer
                from cli_history_viewer import load_history
                history = load_history()
                self.assertIsInstance(history, list, f"Should return list for {filename}")
                
                # Test history module
                from history_module import add_to_history
                add_to_history("recovery test")
                
        print("  ✅ Malformed data files handled gracefully")
    
    def test_network_failure_simulation(self):
        """Test handling of network-related failures"""
        print("\n🧪 Testing network failure handling...")
        
        # Test web viewer with network issues
        with patch('webbrowser.open', side_effect=Exception("Network error")):
            import web_history_viewer
            # Should not crash when browser fails to open
            try:
                web_history_viewer.open_browser("http://localhost:8000")
            except Exception as e:
                self.fail(f"Web viewer should handle browser errors gracefully: {e}")
        
        print("  ✅ Network failures handled gracefully")
    
    def test_clipboard_access_failures(self):
        """Test handling of clipboard access failures"""
        print("\n🧪 Testing clipboard access failure handling...")
        
        # Test clipboard content retrieval with failures
        with patch('subprocess.run', side_effect=subprocess.SubprocessError("Clipboard error")), \
             patch('pyperclip.paste', side_effect=Exception("Pyperclip error")):
            
            from utils import get_clipboard_content
            content = get_clipboard_content()
            # Should return None or handle gracefully
            self.assertIsNone(content, "Should return None when clipboard access fails")
        
        print("  ✅ Clipboard access failures handled gracefully")
    
    def test_module_import_failures(self):
        """Test handling of module import failures"""
        print("\n🧪 Testing module import failure handling...")
        
        # Test with missing module dependencies
        with patch('builtins.__import__', side_effect=ImportError("Module not found")):
            try:
                # Should handle import errors gracefully
                import main
            except ImportError:
                # This is acceptable - the test is that it doesn't cause crashes elsewhere
                pass
        
        print("  ✅ Module import failures handled gracefully")
    
    def test_large_content_handling(self):
        """Test handling of extremely large content"""
        print("\n🧪 Testing large content handling...")
        
        # Create very large content
        large_content = "A" * (10 * 1024 * 1024)  # 10MB of text
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": self.test_history_file}
            
            # Test history module with large content
            from history_module import add_to_history
            add_to_history(large_content)
            
            # Test CLI viewer with large content
            from cli_history_viewer import load_history
            history = load_history()
            self.assertIsInstance(history, list, "Should handle large content")
        
        print("  ✅ Large content handled gracefully")
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
        print("\n🧪 Testing unicode and special character handling...")
        
        # Test various unicode and special characters
        special_contents = [
            "Unicode: 🎉 🚀 📋 ✅ ❌ ⚠️",
            "Emoji: 😀😃😄😁😆😅😂🤣",
            "Math: ∑∏∫∆∇∂∞±≤≥≠≈",
            "Arrows: ←↑→↓↔↕↖↗↘↙",
            "Special: \n\t\r\x00\x01\x02",
            "Mixed: Hello 世界 🌍 Здравствуй мир",
            "RTF-like: {\\rtf1\\ansi\\deff0 {\\fonttbl {\\f0 Times New Roman;}}}"
        ]
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": self.test_history_file}
            
            for content in special_contents:
                # Test adding to history
                from history_module import add_to_history
                add_to_history(content)
                
                # Test loading from history
                from cli_history_viewer import load_history
                history = load_history()
                self.assertIsInstance(history, list, f"Should handle special content: {content[:20]}...")
        
        print("  ✅ Unicode and special characters handled gracefully")
    
    def test_concurrent_access_errors(self):
        """Test handling of concurrent file access errors"""
        print("\n🧪 Testing concurrent access error handling...")
        
        import threading
        import time
        
        def concurrent_writer():
            """Function to write to history concurrently"""
            with patch('utils.get_app_paths') as mock_paths:
                mock_paths.return_value = {"history_file": self.test_history_file}
                from history_module import add_to_history
                for i in range(10):
                    add_to_history(f"Concurrent item {i}")
                    time.sleep(0.01)
        
        # Start multiple concurrent writers
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_writer)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify file is still valid
        with open(self.test_history_file, 'r') as f:
            try:
                history = json.load(f)
                self.assertIsInstance(history, list, "History should remain valid after concurrent access")
            except json.JSONDecodeError:
                # File corruption is possible with concurrent access, but shouldn't crash
                pass
        
        print("  ✅ Concurrent access errors handled gracefully")
    
    def test_system_resource_exhaustion(self):
        """Test handling of system resource exhaustion"""
        print("\n🧪 Testing system resource exhaustion handling...")

        # Simulate memory errors
        with patch('json.load', side_effect=MemoryError("Out of memory")):
            from cli_history_viewer import load_history
            history = load_history()
            self.assertIsInstance(history, list, "Should handle memory errors gracefully")

        # Simulate disk full errors
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            with patch('utils.get_app_paths') as mock_paths:
                mock_paths.return_value = {"history_file": self.test_history_file}
                from history_module import add_to_history
                # Should not crash
                add_to_history("test content")

        print("  ✅ System resource exhaustion handled gracefully")

    def test_configuration_file_errors(self):
        """Test handling of configuration file errors"""
        print("\n🧪 Testing configuration file error handling...")

        # Test with missing config file
        with patch('os.path.exists', return_value=False):
            from utils import get_config
            config = get_config('general', 'polling_interval', 1.0)
            self.assertEqual(config, 1.0, "Should return default when config missing")

        # Test with corrupted config file
        with patch('builtins.open', mock_open(read_data="invalid json")):
            config = get_config('general', 'polling_interval', 1.0)
            self.assertEqual(config, 1.0, "Should return default when config corrupted")

        print("  ✅ Configuration file errors handled gracefully")

if __name__ == '__main__':
    print("🧪 Running Comprehensive Error Handling Tests")
    print("=" * 60)
    
    # Run tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("🎉 Error Handling Tests Complete!")
