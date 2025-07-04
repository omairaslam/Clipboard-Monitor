#!/usr/bin/env python3
"""
Comprehensive configuration tests.
Tests invalid configs, missing files, permission issues, and configuration validation.
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from unittest.mock import patch

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils import get_config
from constants import DEFAULT_CONFIG
from config_manager import ConfigManager

class TestConfiguration(unittest.TestCase):
    """Test configuration handling and validation"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "config.json")
        self.config_manager_patcher = patch('config_manager.CONFIG_PATH', self.config_path)
        self.config_manager_patcher.start()

    def tearDown(self):
        """Clean up test environment"""
        self.config_manager_patcher.stop()
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_valid_configuration_loading(self):
        """Test loading a valid configuration file merges with defaults."""
        print("\n🧪 Testing valid configuration loading...")
        
        user_config = {
            "general": {
                "polling_interval": 2.5,
                "debug_mode": True
            },
            "security": {
                "sanitize_clipboard": False
            }
        }
        with open(self.config_path, 'w') as f:
            json.dump(user_config, f)

        # Manually merge for expectation
        expected_config = json.loads(json.dumps(DEFAULT_CONFIG)) # deep copy
        expected_config['general'].update(user_config['general'])
        expected_config['security'].update(user_config['security'])

        loaded_config = get_config()
        self.assertEqual(loaded_config, expected_config)

        # Test get_section
        self.assertEqual(get_config('general'), expected_config['general'])

        # Test get_config_value
        self.assertEqual(get_config('general', 'polling_interval'), 2.5)
        self.assertEqual(get_config('history', 'max_items'), DEFAULT_CONFIG['history']['max_items'])

        print("  ✅ Valid configuration loaded and merged correctly")

    def test_missing_configuration_file(self):
        """Test that missing config file returns full defaults."""
        print("\n🧪 Testing missing configuration file...")
        
        # Ensure file does not exist
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

        self.assertEqual(get_config(), DEFAULT_CONFIG)
        self.assertEqual(get_config('general'), DEFAULT_CONFIG['general'])
        self.assertEqual(get_config('general', 'polling_interval'), DEFAULT_CONFIG['general']['polling_interval'])
        
        print("  ✅ Missing configuration file handled gracefully")

    def test_corrupted_configuration_file(self):
        """Test that a corrupted config file returns full defaults."""
        print("\n🧪 Testing corrupted configuration files...")
        
        with open(self.config_path, 'w') as f:
            f.write("{'invalid_json': True,}")

        self.assertEqual(get_config(), DEFAULT_CONFIG)
        
        print("  ✅ Corrupted configuration file handled gracefully")

    def test_configuration_file_permissions(self):
        """Test that an unreadable config file returns full defaults."""
        print("\n🧪 Testing configuration file permissions...")
        
        with open(self.config_path, 'w') as f:
            json.dump({"general": {"debug_mode": True}}, f)
        
        os.chmod(self.config_path, 0o000) # No permissions

        # Should fall back to defaults
        self.assertEqual(get_config(), DEFAULT_CONFIG)
        
        # Restore permissions for cleanup
        os.chmod(self.config_path, 0o644)
        
        print("  ✅ Configuration file permission issues handled gracefully")

if __name__ == '__main__':
    unittest.main(verbosity=2)
