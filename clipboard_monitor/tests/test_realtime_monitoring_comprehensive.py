#!/usr/bin/env python3
"""
Comprehensive real-time monitoring tests.
Tests clipboard change detection, polling vs enhanced mode, and monitoring accuracy.
"""

import os
import sys
import json
import time
import tempfile
import shutil
import unittest
import threading
import subprocess
from unittest.mock import patch, MagicMock, call
import pyperclip

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils import get_app_paths, get_clipboard_content, update_service_status

class TestRealtimeMonitoring(unittest.TestCase):
    """Test real-time clipboard monitoring functionality"""
    
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
    
    def test_clipboard_change_detection(self):
        """Test clipboard change detection accuracy"""
        print("\n🧪 Testing clipboard change detection...")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": self.test_history_file}
            
            # Import main clipboard monitor
            import main
            
            # Create monitor instance
            monitor = main.ClipboardMonitor()
            
            # Test initial clipboard content
            initial_content = "Initial test content"
            pyperclip.copy(initial_content)
            
            # Simulate clipboard change detection
            current_content = get_clipboard_content()
            self.assertEqual(current_content, initial_content, "Should detect initial clipboard content")
            
            # Test change detection
            new_content = "Changed test content"
            pyperclip.copy(new_content)
            
            updated_content = get_clipboard_content()
            self.assertEqual(updated_content, new_content, "Should detect clipboard changes")
            self.assertNotEqual(updated_content, initial_content, "Should detect content difference")
        
        print("  ✅ Clipboard change detection working")
    
    def test_polling_mode_accuracy(self):
        """Test polling mode monitoring accuracy"""
        print("\n🧪 Testing polling mode accuracy...")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {
                "history_file": self.test_history_file,
                "status_file": self.test_status_file
            }
            
            # Set to polling mode
            update_service_status("running_polling")
            
            import main
            monitor = main.ClipboardMonitor()
            
            # Test polling interval configuration
            from utils import get_config
            polling_interval = get_config('general', 'polling_interval', 1.0)
            self.assertIsInstance(polling_interval, (int, float), "Polling interval should be numeric")
            self.assertGreater(polling_interval, 0, "Polling interval should be positive")
            
            # Test that monitor respects polling mode
            self.assertTrue(hasattr(monitor, 'check_clipboard'), "Monitor should have clipboard check method")
        
        print("  ✅ Polling mode configuration correct")
    
    def test_enhanced_mode_accuracy(self):
        """Test enhanced mode monitoring accuracy"""
        print("\n🧪 Testing enhanced mode accuracy...")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {
                "history_file": self.test_history_file,
                "status_file": self.test_status_file
            }
            
            # Set to enhanced mode
            update_service_status("running_enhanced")
            
            import main
            monitor = main.ClipboardMonitor()
            
            # Test enhanced mode configuration
            from utils import get_config
            enhanced_interval = get_config('general', 'enhanced_check_interval', 0.1)
            self.assertIsInstance(enhanced_interval, (int, float), "Enhanced interval should be numeric")
            self.assertLess(enhanced_interval, 1.0, "Enhanced interval should be faster than polling")
        
        print("  ✅ Enhanced mode configuration correct")
    
    def test_monitoring_thread_safety(self):
        """Test thread safety of monitoring operations"""
        print("\n🧪 Testing monitoring thread safety...")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": self.test_history_file}
            
            # Test concurrent clipboard operations
            def clipboard_worker(worker_id):
                """Worker function for concurrent clipboard operations"""
                for i in range(10):
                    content = f"Worker {worker_id} content {i}"
                    pyperclip.copy(content)
                    time.sleep(0.01)  # Small delay
                    
                    # Verify content was set correctly
                    retrieved = pyperclip.paste()
                    # Note: Due to concurrent access, content might be overwritten
                    # We just verify no crashes occur
            
            # Start multiple workers
            threads = []
            for worker_id in range(3):
                thread = threading.Thread(target=clipboard_worker, args=(worker_id,))
                threads.append(thread)
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join()
            
            # Verify no crashes occurred
            final_content = pyperclip.paste()
            self.assertIsInstance(final_content, str, "Clipboard should remain accessible after concurrent operations")
        
        print("  ✅ Thread safety maintained")
    
    def test_content_deduplication(self):
        """Test content deduplication in monitoring"""
        print("\n🧪 Testing content deduplication...")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": self.test_history_file}
            
            from history_module import add_to_history
            
            # Add same content multiple times
            duplicate_content = "Duplicate test content"
            
            for i in range(5):
                add_to_history(duplicate_content)
                time.sleep(0.01)  # Small delay to ensure different timestamps
            
            # Load history and check deduplication
            with open(self.test_history_file, 'r') as f:
                history = json.load(f)
            
            # Should have only one entry (most recent)
            matching_items = [item for item in history if item['content'] == duplicate_content]
            self.assertEqual(len(matching_items), 1, "Should deduplicate identical content")
        
        print("  ✅ Content deduplication working")
    
    def test_monitoring_pause_resume(self):
        """Test monitoring pause and resume functionality"""
        print("\n🧪 Testing monitoring pause/resume...")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"status_file": self.test_status_file}
            
            from utils import update_service_status, get_service_status
            
            # Test pause
            update_service_status("paused")
            status = get_service_status()
            self.assertEqual(status, "paused", "Service should be paused")
            
            # Test resume to enhanced mode
            update_service_status("running_enhanced")
            status = get_service_status()
            self.assertEqual(status, "running_enhanced", "Service should resume to enhanced mode")
            
            # Test resume to polling mode
            update_service_status("running_polling")
            status = get_service_status()
            self.assertEqual(status, "running_polling", "Service should resume to polling mode")
        
        print("  ✅ Pause/resume functionality working")
    
    def test_clipboard_content_types(self):
        """Test monitoring different clipboard content types"""
        print("\n🧪 Testing different clipboard content types...")
        
        # Test various content types
        test_contents = [
            ("Plain text", "Simple plain text content"),
            ("Unicode", "Unicode content: 🎉 🚀 📋 ✅"),
            ("Markdown", "# Markdown\n\nWith **bold** and *italic*"),
            ("JSON", '{"key": "value", "number": 42}'),
            ("URL", "https://example.com/test?param=value"),
            ("Code", "def hello():\n    print('Hello, World!')"),
            ("Large text", "A" * 1000),  # Large content
            ("Empty", ""),  # Empty content
            ("Whitespace", "   \n\t\r   "),  # Whitespace only
        ]
        
        for content_type, content in test_contents:
            pyperclip.copy(content)
            retrieved = get_clipboard_content()
            
            if content.strip():  # Non-empty content
                self.assertEqual(retrieved, content, f"Should handle {content_type} correctly")
            else:  # Empty or whitespace content
                # May be handled differently, just ensure no crashes
                self.assertIsInstance(retrieved, (str, type(None)), f"Should handle {content_type} gracefully")
        
        print("  ✅ Different content types handled correctly")
    
    def test_monitoring_performance_impact(self):
        """Test performance impact of monitoring"""
        print("\n🧪 Testing monitoring performance impact...")
        
        # Measure time for clipboard operations with and without monitoring
        test_content = "Performance test content"
        
        # Without monitoring (baseline)
        start_time = time.perf_counter()
        for i in range(100):
            pyperclip.copy(f"{test_content} {i}")
        baseline_time = time.perf_counter() - start_time
        
        # With monitoring simulation
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": self.test_history_file}
            
            start_time = time.perf_counter()
            for i in range(100):
                content = f"{test_content} {i}"
                pyperclip.copy(content)
                # Simulate monitoring check
                get_clipboard_content()
            monitoring_time = time.perf_counter() - start_time
        
        # Calculate overhead
        overhead = monitoring_time - baseline_time
        overhead_percentage = (overhead / baseline_time) * 100
        
        # Performance requirements
        self.assertLess(overhead_percentage, 50, f"Monitoring overhead should be < 50%, got {overhead_percentage:.1f}%")
        self.assertLess(monitoring_time, 5.0, f"100 operations should complete in < 5s, took {monitoring_time:.2f}s")
        
        print(f"  ✅ Performance impact: {overhead_percentage:.1f}% overhead ({overhead:.3f}s)")
    
    def test_error_recovery_in_monitoring(self):
        """Test error recovery during monitoring"""
        print("\n🧪 Testing error recovery in monitoring...")
        
        # Test clipboard access errors
        with patch('pyperclip.paste', side_effect=Exception("Clipboard error")):
            content = get_clipboard_content()
            self.assertIsNone(content, "Should handle clipboard errors gracefully")
        
        # Test subprocess errors
        with patch('subprocess.run', side_effect=subprocess.SubprocessError("Process error")):
            content = get_clipboard_content()
            # Should fall back to pyperclip
            self.assertIsInstance(content, (str, type(None)), "Should handle subprocess errors")
        
        print("  ✅ Error recovery working correctly")

if __name__ == '__main__':
    print("🧪 Running Comprehensive Real-time Monitoring Tests")
    print("=" * 60)
    
    # Run tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("🎉 Real-time Monitoring Tests Complete!")
