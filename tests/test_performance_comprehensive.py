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

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import modules.history_module

class TestPerformance(unittest.TestCase):
    """Test performance characteristics of the application"""

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
        # Assert that history is empty after clearing
        self.assertEqual(len(modules.history_module.load_history()), 0, "History should be empty after clear_history in setUp")
        gc.collect()

    def tearDown(self):
        """Clean up test environment"""
        self.config_patcher.stop()
        shutil.rmtree(self.test_dir)
        gc.collect()

    def measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage of a function"""
        process = psutil.Process(os.getpid())
        gc.collect()
        mem_before = process.memory_info().rss
        result = func(*args, **kwargs)
        gc.collect()
        mem_after = process.memory_info().rss
        return result, mem_after - mem_before

    def test_large_history_performance(self):
        """Test performance with large history files"""
        print("\n🧪 Testing large history performance...")
        
        large_history = [{"content": f"item {i}", "timestamp": time.time() - i} for i in range(1000)]
        with open(self.history_file, 'w') as f:
            json.dump(large_history, f)

        _, exec_time = self.measure_execution_time(modules.history_module.load_history)
        self.assertLess(exec_time, 1.0, f"Loading 1k items took too long: {exec_time:.2f}s")

        _, memory_used = self.measure_memory_usage(modules.history_module.load_history)
        self.assertLess(memory_used, 50 * 1024 * 1024, f"Memory usage for 1k items is too high: {memory_used / 1024**2:.2f}MB")
        
        print(f"  ✅ Large history loaded in {exec_time:.2f}s using {memory_used / 1024**2:.2f}MB")

    def test_rapid_history_additions(self):
        """Test performance of rapid history additions"""
        print("\n🧪 Testing rapid history additions...")
        
        _, exec_time = self.measure_execution_time(
            lambda: [modules.history_module.add_to_history(f"item {i}") for i in range(100)]
        )
        
        self.assertLess(exec_time, 5.0, f"Adding 100 items took too long: {exec_time:.2f}s")
        
        history = modules.history_module.load_history()
        self.assertEqual(len(history), 100)
        
        print(f"  ✅ Added 100 items in {exec_time:.2f}s")

    def test_concurrent_operations_performance(self):
        """Test performance under concurrent operations"""
        print("\n🧪 Testing concurrent operations performance...")

        def worker(worker_id):
            for i in range(10):
                modules.history_module.add_to_history(f"worker {worker_id} item {i}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        
        _, exec_time = self.measure_execution_time(lambda: [t.start() for t in threads] and [t.join() for t in threads])

        self.assertLess(exec_time, 5.0, f"Concurrent additions took too long: {exec_time:.2f}s")
        
        history = modules.history_module.load_history()
        self.assertEqual(len(history), 50)
        
        print(f"  ✅ 5 workers added 10 items each in {exec_time:.2f}s")

    def measure_execution_time(self, func, *args, **kwargs):
        """Measure execution time of a function"""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        return result, end_time - start_time

if __name__ == '__main__':
    unittest.main(verbosity=2)
