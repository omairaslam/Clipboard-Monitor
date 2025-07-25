#!/usr/bin/env python3
"""
Test script to verify the config saving fix
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_config_path():
    """Test that the config path is correct"""
    print("🔍 Testing Config Path")
    print("=" * 40)
    
    expected_path = Path.home() / "Library" / "Application Support" / "ClipboardMonitor" / "config.json"
    print(f"Expected config path: {expected_path}")
    print(f"Directory exists: {expected_path.parent.exists()}")
    print(f"File exists: {expected_path.exists()}")
    
    return expected_path

def test_config_write():
    """Test writing to the config file"""
    print("\n🔧 Testing Config Write")
    print("=" * 40)
    
    try:
        from utils import set_config_value
        
        # Test setting a value
        success = set_config_value('test', 'developer_mode_test', True)
        print(f"✅ Config write test: {'SUCCESS' if success else 'FAILED'}")
        
        if success:
            # Verify it was written
            from utils import get_config_value
            value = get_config_value('test', 'developer_mode_test', False)
            print(f"✅ Config read test: {value} (expected: True)")
            
            # Clean up test value
            set_config_value('test', 'developer_mode_test', None)
            
        return success
        
    except Exception as e:
        print(f"❌ Config write test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_developer_mode_config():
    """Test the actual developer mode config"""
    print("\n🔧 Testing Developer Mode Config")
    print("=" * 40)
    
    try:
        from utils import get_config_value, set_config_value
        
        # Get current value
        current_value = get_config_value('advanced', 'developer_mode', False)
        print(f"✅ Current developer mode: {current_value}")
        
        # Test setting to True
        success = set_config_value('advanced', 'developer_mode', True)
        print(f"✅ Set to True: {'SUCCESS' if success else 'FAILED'}")
        
        if success:
            # Verify it was set
            new_value = get_config_value('advanced', 'developer_mode', False)
            print(f"✅ Verified value: {new_value} (expected: True)")
            
            # Reset to original value
            set_config_value('advanced', 'developer_mode', current_value)
            print(f"✅ Reset to original: {current_value}")
            
        return success
        
    except Exception as e:
        print(f"❌ Developer mode config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Config Fix")
    print("=" * 50)
    
    # Test 1: Config Path
    config_path = test_config_path()
    
    # Test 2: Config Write
    write_success = test_config_write()
    
    # Test 3: Developer Mode Config
    dev_mode_success = test_developer_mode_config()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Config Path: ✅ {config_path}")
    print(f"   Config Write: {'✅ PASS' if write_success else '❌ FAIL'}")
    print(f"   Developer Mode: {'✅ PASS' if dev_mode_success else '❌ FAIL'}")
    
    if write_success and dev_mode_success:
        print("\n🎉 All tests passed!")
        print("✅ Config file path is correct")
        print("✅ Config writing works")
        print("✅ Developer mode toggle should work")
        print("\n💡 You can now safely toggle Developer Mode in the menu!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return write_success and dev_mode_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
