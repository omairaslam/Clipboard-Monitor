#!/usr/bin/env python3
"""
Test that the fixed menu bar app can toggle developer mode without errors
"""

import sys
import os
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_config_path_fix():
    """Test that the config path is now correct"""
    print("🔍 Testing Config Path Fix")
    print("=" * 40)
    
    try:
        from utils import set_config_value
        
        # Test that we can write without permission errors
        success = set_config_value('test_fix', 'permission_test', True)
        print(f"✅ Config write (no permission error): {'SUCCESS' if success else 'FAILED'}")
        
        # Verify it was written to the correct location
        config_path = Path.home() / "Library" / "Application Support" / "ClipboardMonitor" / "config.json"
        if config_path.exists():
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            if 'test_fix' in config and config['test_fix'].get('permission_test') == True:
                print(f"✅ Config written to correct location: {config_path}")
                
                # Clean up test data
                set_config_value('test_fix', 'permission_test', None)
                return True
            else:
                print(f"❌ Config not found in expected location")
                return False
        else:
            print(f"❌ Config file not found at: {config_path}")
            return False
            
    except Exception as e:
        print(f"❌ Config path test failed: {e}")
        return False

def test_json_error_fix():
    """Test that the JSON error is fixed"""
    print("\n🔧 Testing JSON Error Fix")
    print("=" * 40)
    
    try:
        from utils import set_config_value
        
        # This should not raise a JSONEncodeError anymore
        success = set_config_value('test_json', 'json_test', {'complex': 'data', 'number': 42})
        print(f"✅ Complex JSON write (no JSON error): {'SUCCESS' if success else 'FAILED'}")
        
        if success:
            # Clean up
            set_config_value('test_json', 'json_test', None)
            
        return success
        
    except AttributeError as e:
        if "JSONEncodeError" in str(e):
            print(f"❌ JSON error still exists: {e}")
            return False
        else:
            print(f"❌ Unexpected AttributeError: {e}")
            return False
    except Exception as e:
        print(f"❌ JSON test failed: {e}")
        return False

def test_developer_mode_setting():
    """Test the developer mode setting specifically"""
    print("\n🔧 Testing Developer Mode Setting")
    print("=" * 40)
    
    try:
        from utils import set_config_value, get_config
        
        # Get current value
        current_value = get_config('advanced', 'developer_mode', False)
        print(f"   Current developer mode: {current_value}")
        
        # Try to toggle it
        new_value = not current_value
        success = set_config_value('advanced', 'developer_mode', new_value)
        print(f"✅ Toggle developer mode: {'SUCCESS' if success else 'FAILED'}")
        
        if success:
            # Reset to original
            set_config_value('advanced', 'developer_mode', current_value)
            print(f"✅ Reset to original value: {current_value}")
            
        return success
        
    except Exception as e:
        print(f"❌ Developer mode test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Fixed Developer Mode Toggle")
    print("=" * 50)
    
    # Test 1: Config path fix
    path_success = test_config_path_fix()
    
    # Test 2: JSON error fix
    json_success = test_json_error_fix()
    
    # Test 3: Developer mode setting
    dev_mode_success = test_developer_mode_setting()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Config Path Fix: {'✅ PASS' if path_success else '❌ FAIL'}")
    print(f"   JSON Error Fix: {'✅ PASS' if json_success else '❌ FAIL'}")
    print(f"   Developer Mode: {'✅ PASS' if dev_mode_success else '❌ FAIL'}")
    
    if path_success and json_success and dev_mode_success:
        print("\n🎉 All fixes verified!")
        print("✅ Permission error fixed")
        print("✅ JSON error fixed")
        print("✅ Developer mode toggle ready")
        
        print("\n🚀 The menu bar app should now work perfectly!")
        print("   Try toggling Developer Mode in:")
        print("   Settings → Advanced Settings → 🔧 Developer Mode")
    else:
        print("\n⚠️  Some fixes may not be working. Check the output above.")
    
    return path_success and json_success and dev_mode_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
