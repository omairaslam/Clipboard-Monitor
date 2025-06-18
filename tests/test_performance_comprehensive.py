#!/usr/bin/env python3
"""
Comprehensive performance tests.
Tests large datasets, memory usage, response times, and concurrent operations.
"""

import os
import sys
import json
import time
import tempfile
import shutil
import unittest
import threading
import psutil
import gc
from unittest.mock import patch
import statistics

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils import get_app_paths

class TestPerformance(unittest.TestCase):
    """Test performance characteristics of the application"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_history_file = os.path.join(self.test_dir, "test_history.json")
        
        # Initialize empty history
        with open(self.test_history_file, 'w') as f:
            json.dump([], f)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        gc.collect()  # Force garbage collection
    
    def measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage of a function"""
        process = psutil.Process()
        
        # Force garbage collection before measurement
        gc.collect()
        memory_before = process.memory_info().rss
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Force garbage collection after execution
        gc.collect()
        memory_after = process.memory_info().rss
        
        memory_used = memory_after - memory_before
        return result, memory_used
    
    def measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function"""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        return result, execution_time
    
    def test_large_history_performance(self):
        """Test performance with large history files"""
        print("\n🧪 Testing large history performance...")
        
        # Create large history (10,000 items)
        large_history = []
        for i in range(10000):
            large_history.append({
                "content": f"Test item {i} with some longer content to simulate real usage patterns",
                "timestamp": time.time() - (10000 - i)
            })
        
        with open(self.test_history_file, 'w') as f:
            json.dump(large_history, f)
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": self.test_history_file}
            
            # Test CLI history viewer performance
            from cli_history_viewer import load_history
            
            result, exec_time = self.measure_execution_time(load_history)
            result, memory_used = self.measure_memory_usage(load_history)
            
            self.assertEqual(len(result), 10000, "Should load all 10,000 items")
            self.assertLess(exec_time, 5.0, f"Loading 10k items should take < 5s, took {exec_time:.2f}s")
            self.assertLess(memory_used, 100 * 1024 * 1024, f"Memory usage should be < 100MB, used {memory_used / 1024 / 1024:.2f}MB")
        
        print(f"  ✅ Large history loaded in {exec_time:.2f}s using {memory_used / 1024 / 1024:.2f}MB")
    
    def test_rapid_history_additions(self):
        """Test performance of rapid history additions"""
        print("\n🧪 Testing rapid history additions...")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": self.test_history_file}
            
            from history_module import add_to_history
            
            # Measure time to add 1000 items rapidly
            start_time = time.perf_counter()
            
            for i in range(1000):
                add_to_history(f"Rapid test item {i}")
            
            end_time = time.perf_counter()
            total_time = end_time - start_time
            
            # Verify all items were added
            with open(self.test_history_file, 'r') as f:
                history = json.load(f)
            
            self.assertEqual(len(history), 1000, "Should have added all 1000 items")
            self.assertLess(total_time, 10.0, f"Adding 1000 items should take < 10s, took {total_time:.2f}s")
            
            # Calculate items per second
            items_per_second = 1000 / total_time
            self.assertGreater(items_per_second, 100, f"Should process > 100 items/sec, got {items_per_second:.1f}")
        
        print(f"  ✅ Added 1000 items in {total_time:.2f}s ({items_per_second:.1f} items/sec)")
    
    def test_concurrent_operations_performance(self):
        """Test performance under concurrent operations"""
        print("\n🧪 Testing concurrent operations performance...")
        
        def concurrent_worker(worker_id, num_items):
            """Worker function for concurrent testing"""
            with patch('utils.get_app_paths') as mock_paths:
                mock_paths.return_value = {"history_file": self.test_history_file}
                from history_module import add_to_history
                
                for i in range(num_items):
                    add_to_history(f"Worker {worker_id} item {i}")
        
        # Start multiple concurrent workers
        num_workers = 5
        items_per_worker = 100
        
        start_time = time.perf_counter()
        
        threads = []
        for worker_id in range(num_workers):
            thread = threading.Thread(target=concurrent_worker, args=(worker_id, items_per_worker))
            threads.append(thread)
            thread.start()
        
        # Wait for all workers to complete
        for thread in threads:
            thread.join()
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Verify results
        with open(self.test_history_file, 'r') as f:
            history = json.load(f)
        
        expected_items = num_workers * items_per_worker
        actual_items = len(history)
        
        # Allow for some data loss due to concurrent access
        self.assertGreaterEqual(actual_items, expected_items * 0.8, 
                               f"Should have at least 80% of expected items ({expected_items}), got {actual_items}")
        
        print(f"  ✅ Concurrent operations: {actual_items}/{expected_items} items in {total_time:.2f}s")
    
    def test_memory_usage_patterns(self):
        """Test memory usage patterns over time"""
        print("\n🧪 Testing memory usage patterns...")
        
        process = psutil.Process()
        memory_measurements = []
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": self.test_history_file}
            
            from history_module import add_to_history
            from cli_history_viewer import load_history
            
            # Measure memory usage over multiple operations
            for cycle in range(10):
                # Add items
                for i in range(100):
                    add_to_history(f"Memory test cycle {cycle} item {i}")
                
                # Load history
                history = load_history()
                
                # Measure memory
                gc.collect()
                memory_used = process.memory_info().rss
                memory_measurements.append(memory_used)
                
                # Clear some history to test memory cleanup
                if cycle % 3 == 0:
                    with open(self.test_history_file, 'w') as f:
                        json.dump([], f)
        
        # Analyze memory usage patterns
        memory_mb = [m / 1024 / 1024 for m in memory_measurements]
        avg_memory = statistics.mean(memory_mb)
        max_memory = max(memory_mb)
        memory_growth = memory_mb[-1] - memory_mb[0]
        
        self.assertLess(avg_memory, 200, f"Average memory usage should be < 200MB, got {avg_memory:.2f}MB")
        self.assertLess(max_memory, 300, f"Peak memory usage should be < 300MB, got {max_memory:.2f}MB")
        self.assertLess(abs(memory_growth), 50, f"Memory growth should be < 50MB, got {memory_growth:.2f}MB")
        
        print(f"  ✅ Memory usage: avg={avg_memory:.1f}MB, max={max_memory:.1f}MB, growth={memory_growth:.1f}MB")
    
    def test_response_time_consistency(self):
        """Test response time consistency"""
        print("\n🧪 Testing response time consistency...")
        
        with patch('utils.get_app_paths') as mock_paths:
            mock_paths.return_value = {"history_file": self.test_history_file}
            
            from history_module import add_to_history
            from cli_history_viewer import load_history
            
            # Measure response times for multiple operations
            add_times = []
            load_times = []
            
            for i in range(50):
                # Measure add time
                start_time = time.perf_counter()
                add_to_history(f"Response time test item {i}")
                add_time = time.perf_counter() - start_time
                add_times.append(add_time)
                
                # Measure load time every 10 items
                if i % 10 == 0:
                    start_time = time.perf_counter()
                    history = load_history()
                    load_time = time.perf_counter() - start_time
                    load_times.append(load_time)
            
            # Analyze response times
            avg_add_time = statistics.mean(add_times)
            max_add_time = max(add_times)
            add_time_stdev = statistics.stdev(add_times)
            
            avg_load_time = statistics.mean(load_times)
            max_load_time = max(load_times)
            
            # Response time requirements
            self.assertLess(avg_add_time, 0.1, f"Average add time should be < 100ms, got {avg_add_time*1000:.1f}ms")
            self.assertLess(max_add_time, 0.5, f"Max add time should be < 500ms, got {max_add_time*1000:.1f}ms")
            self.assertLess(add_time_stdev, 0.05, f"Add time consistency should be good (stdev < 50ms), got {add_time_stdev*1000:.1f}ms")
            
            self.assertLess(avg_load_time, 1.0, f"Average load time should be < 1s, got {avg_load_time:.2f}s")
            self.assertLess(max_load_time, 2.0, f"Max load time should be < 2s, got {max_load_time:.2f}s")
        
        print(f"  ✅ Response times: add={avg_add_time*1000:.1f}ms±{add_time_stdev*1000:.1f}ms, load={avg_load_time*1000:.1f}ms")

if __name__ == '__main__':
    print("🧪 Running Comprehensive Performance Tests")
    print("=" * 60)
    
    # Check if psutil is available
    try:
        import psutil
    except ImportError:
        print("⚠️  psutil not available, some memory tests will be skipped")
        print("   Install with: pip install psutil")
    
    # Run tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("🎉 Performance Tests Complete!")
