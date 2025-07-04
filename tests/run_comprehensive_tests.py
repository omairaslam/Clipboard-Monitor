#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner
"""

import unittest
import os
import sys
import tempfile
import json

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def run_tests():
    """Run all comprehensive tests."""
    # Create a temporary directory for test artifacts
    with tempfile.TemporaryDirectory() as test_dir:
        # Create a temporary config file
        config_path = os.path.join(test_dir, "config.json")
        history_path = os.path.join(test_dir, "history.json")
        with open(config_path, 'w') as f:
            json.dump({"history": {"save_location": history_path}}, f)

        # Set environment variable for tests to use
        os.environ['CLIPBOARD_MONITOR_CONFIG_PATH'] = config_path

        # Discover and run tests
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir=current_dir, pattern='test_*_comprehensive.py')
        
        # Create a test runner
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Clean up environment variable
        del os.environ['CLIPBOARD_MONITOR_CONFIG_PATH']

        # Exit with a non-zero code if tests failed
        if not result.wasSuccessful():
            sys.exit(1)

if __name__ == '__main__':
    # Check for psutil
    try:
        import psutil
        print("✅ psutil available for performance tests")
    except ImportError:
        print("⚠️  psutil not available, some memory tests will be skipped")
        print("   Install with: pip install psutil")
        
    print("🚀 Starting Comprehensive Test Suite")
    run_tests()
    print("🎉 Comprehensive Test Suite Complete!")
