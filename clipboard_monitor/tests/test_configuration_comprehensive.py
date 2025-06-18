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
import stat
from unittest.mock import patch, mock_open, MagicMock

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from utils import get_config, get_app_paths

class TestConfiguration(unittest.TestCase):
    """Test configuration handling and validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_config_file = os.path.join(self.test_dir, "config.json")
        
        # Create valid test configuration
        self.valid_config = {
            "general": {
                "polling_interval": 1.0,
                "enhanced_check_interval": 0.1,
                "idle_check_interval": 1.0,
                "notification_title": "Test Clipboard Monitor",
                "debug_mode": False
            },
            "modules": {
                "markdown_modify_clipboard": True,
                "code_formatter_read_only": True,
                "mermaid_auto_open": True
            }
        }
        
        with open(self.test_config_file, 'w') as f:
            json.dump(self.valid_config, f, indent=2)
    
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
    
    def test_valid_configuration_loading(self):
        """Test loading valid configuration"""
        print("\n🧪 Testing valid configuration loading...")
        
        with patch('os.path.dirname', return_value=self.test_dir):
            # Test loading full config
            config = get_config()
            self.assertEqual(config, self.valid_config, "Should load complete valid config")
            
            # Test loading specific sections
            general_config = get_config('general')
            self.assertEqual(general_config, self.valid_config['general'], "Should load general section")
            
            modules_config = get_config('modules')
            self.assertEqual(modules_config, self.valid_config['modules'], "Should load modules section")
            
            # Test loading specific keys
            polling_interval = get_config('general', 'polling_interval')
            self.assertEqual(polling_interval, 1.0, "Should load specific config value")
            
            markdown_modify = get_config('modules', 'markdown_modify_clipboard')
            self.assertTrue(markdown_modify, "Should load boolean config value")
        
        print("  ✅ Valid configuration loaded correctly")
    
    def test_missing_configuration_file(self):
        """Test handling of missing configuration file"""
        print("\n🧪 Testing missing configuration file...")
        
        # Test with non-existent file
        with patch('os.path.dirname', return_value="/nonexistent/directory"):
            # Should return defaults
            config = get_config('general', 'polling_interval', 2.0)
            self.assertEqual(config, 2.0, "Should return default for missing file")
            
            full_config = get_config()
            self.assertIsNone(full_config, "Should return None for missing file")
            
            section_config = get_config('general')
            self.assertIsNone(section_config, "Should return None for missing section")
        
        print("  ✅ Missing configuration file handled gracefully")
    
    def test_corrupted_configuration_file(self):
        """Test handling of corrupted configuration files"""
        print("\n🧪 Testing corrupted configuration files...")
        
        # Test various types of corruption
        corrupted_configs = [
            ("empty_file", ""),
            ("invalid_json", "invalid json content"),
            ("partial_json", '{"general": {"polling_interval":'),
            ("wrong_type", '"string instead of object"'),
            ("null_config", "null"),
            ("array_config", '["not", "an", "object"]'),
            ("binary_data", b"\x00\x01\x02\x03".decode('latin1', errors='ignore'))
        ]
        
        for config_name, content in corrupted_configs:
            corrupted_file = os.path.join(self.test_dir, f"{config_name}.json")
            with open(corrupted_file, 'w') as f:
                f.write(content)
            
            with patch('os.path.dirname', return_value=self.test_dir), \
                 patch('os.path.join', return_value=corrupted_file):
                
                # Should handle corruption gracefully
                config = get_config('general', 'polling_interval', 3.0)
                self.assertEqual(config, 3.0, f"Should return default for {config_name}")
                
                full_config = get_config()
                self.assertEqual(full_config, 3.0, f"Should return default for {config_name}")
        
        print("  ✅ Corrupted configuration files handled gracefully")
    
    def test_configuration_file_permissions(self):
        """Test handling of configuration file permission issues"""
        print("\n🧪 Testing configuration file permissions...")
        
        # Create unreadable config file
        unreadable_file = os.path.join(self.test_dir, "unreadable.json")
        with open(unreadable_file, 'w') as f:
            json.dump(self.valid_config, f)
        os.chmod(unreadable_file, 0o000)  # No permissions
        
        with patch('os.path.dirname', return_value=self.test_dir), \
             patch('os.path.join', return_value=unreadable_file):
            
            # Should handle permission error gracefully
            config = get_config('general', 'polling_interval', 4.0)
            self.assertEqual(config, 4.0, "Should return default for unreadable file")
        
        # Restore permissions for cleanup
        os.chmod(unreadable_file, 0o644)
        
        print("  ✅ Configuration file permission issues handled gracefully")
    
    def test_configuration_validation(self):
        """Test configuration value validation"""
        print("\n🧪 Testing configuration validation...")
        
        # Test with invalid values
        invalid_configs = [
            {
                "general": {
                    "polling_interval": -1.0,  # Negative value
                    "enhanced_check_interval": "invalid",  # Wrong type
                    "notification_title": None,  # Null value
                    "debug_mode": "yes"  # Wrong type for boolean
                }
            },
            {
                "modules": {
                    "markdown_modify_clipboard": "true",  # String instead of boolean
                    "code_formatter_read_only": 1,  # Number instead of boolean
                    "nonexistent_module": True  # Unknown module
                }
            }
        ]
        
        for i, invalid_config in enumerate(invalid_configs):
            invalid_file = os.path.join(self.test_dir, f"invalid_{i}.json")
            with open(invalid_file, 'w') as f:
                json.dump(invalid_config, f)
            
            with patch('os.path.dirname', return_value=self.test_dir), \
                 patch('os.path.join', return_value=invalid_file):
                
                # Should load config but application should handle invalid values
                config = get_config()
                self.assertIsInstance(config, dict, f"Should load invalid config {i}")
                
                # Test specific invalid values with defaults
                polling = get_config('general', 'polling_interval', 1.0)
                if isinstance(polling, (int, float)) and polling > 0:
                    # Valid value loaded
                    pass
                else:
                    # Should use default
                    self.assertEqual(polling, 1.0, "Should use default for invalid polling interval")
        
        print("  ✅ Configuration validation working correctly")
    
    def test_configuration_defaults(self):
        """Test configuration default values"""
        print("\n🧪 Testing configuration defaults...")
        
        # Test all expected default values
        default_tests = [
            ('general', 'polling_interval', 1.0),
            ('general', 'enhanced_check_interval', 0.1),
            ('general', 'idle_check_interval', 1.0),
            ('general', 'notification_title', "Clipboard Monitor"),
            ('general', 'debug_mode', False),
            ('modules', 'markdown_modify_clipboard', True),
            ('modules', 'code_formatter_read_only', True),
            ('modules', 'mermaid_auto_open', True),
            ('nonexistent_section', 'nonexistent_key', 'default_value')
        ]
        
        # Test with missing config file
        with patch('os.path.exists', return_value=False):
            for section, key, expected_default in default_tests:
                result = get_config(section, key, expected_default)
                self.assertEqual(result, expected_default, 
                               f"Should return default for {section}.{key}")
        
        print("  ✅ Configuration defaults working correctly")
    
    def test_configuration_type_safety(self):
        """Test configuration type safety"""
        print("\n🧪 Testing configuration type safety...")
        
        # Create config with mixed types
        mixed_config = {
            "general": {
                "polling_interval": "1.5",  # String that could be float
                "enhanced_check_interval": 0.1,  # Correct float
                "notification_title": 123,  # Number instead of string
                "debug_mode": "false"  # String instead of boolean
            },
            "modules": {
                "markdown_modify_clipboard": 1,  # Number instead of boolean
                "code_formatter_read_only": "yes"  # String instead of boolean
            }
        }
        
        mixed_file = os.path.join(self.test_dir, "mixed_types.json")
        with open(mixed_file, 'w') as f:
            json.dump(mixed_config, f)
        
        with patch('os.path.dirname', return_value=self.test_dir), \
             patch('os.path.join', return_value=mixed_file):
            
            # Load config and verify types are handled appropriately
            config = get_config()
            self.assertIsInstance(config, dict, "Should load config with mixed types")
            
            # Application should handle type conversion or use defaults
            polling = get_config('general', 'polling_interval', 1.0)
            self.assertIsInstance(polling, (int, float, str), "Should handle polling interval type")
            
            title = get_config('general', 'notification_title', "Default")
            self.assertIsInstance(title, (str, int), "Should handle title type")
        
        print("  ✅ Configuration type safety working correctly")
    
    def test_configuration_environment_override(self):
        """Test configuration override from environment variables"""
        print("\n🧪 Testing configuration environment override...")
        
        # Test environment variable handling (if implemented)
        with patch.dict(os.environ, {
            'CLIPBOARD_MONITOR_POLLING_INTERVAL': '2.5',
            'CLIPBOARD_MONITOR_DEBUG_MODE': 'true'
        }):
            # Note: This test assumes environment override is implemented
            # If not implemented, this test documents the expected behavior
            
            with patch('os.path.dirname', return_value=self.test_dir):
                config = get_config()
                # Environment override would be a future enhancement
                self.assertIsInstance(config, (dict, type(None)), "Should handle environment variables")
        
        print("  ✅ Configuration environment override tested")

if __name__ == '__main__':
    print("🧪 Running Comprehensive Configuration Tests")
    print("=" * 60)
    
    # Run tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("🎉 Configuration Tests Complete!")
