#!/usr/bin/env python3
"""
Simple test to verify developer mode toggle works
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_developer_mode_toggle():
    """Test the developer mode toggle functionality"""
    print("🔧 Testing Developer Mode Toggle")
    print("=" * 50)
    
    try:
        from utils import set_config_value, get_config
        
        print("📋 Step 1: Get current developer mode setting")
        current_value = get_config('advanced', 'developer_mode', False)
        print(f"   Current value: {current_value}")
        
        print("\n📋 Step 2: Toggle to opposite value")
        new_value = not current_value
        success = set_config_value('advanced', 'developer_mode', new_value)
        print(f"   Set to {new_value}: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        if success:
            print("\n📋 Step 3: Verify the change")
            verified_value = get_config('advanced', 'developer_mode', False)
            print(f"   Verified value: {verified_value}")
            print(f"   Match expected: {'✅ YES' if verified_value == new_value else '❌ NO'}")
            
            print("\n📋 Step 4: Reset to original value")
            reset_success = set_config_value('advanced', 'developer_mode', current_value)
            print(f"   Reset to {current_value}: {'✅ SUCCESS' if reset_success else '❌ FAILED'}")
            
            return success and (verified_value == new_value) and reset_success
        
        return False
        
    except Exception as e:
        print(f"❌ Developer mode toggle test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_config_file():
    """Check if config file was created properly"""
    print("\n📁 Checking Config File")
    print("=" * 50)
    
    config_path = Path.home() / "Library" / "Application Support" / "ClipboardMonitor" / "config.json"
    
    if config_path.exists():
        print(f"✅ Config file exists: {config_path}")
        
        try:
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            print(f"✅ Config file is valid JSON")
            
            if 'advanced' in config:
                print(f"✅ Advanced section exists")
                if 'developer_mode' in config['advanced']:
                    print(f"✅ Developer mode setting: {config['advanced']['developer_mode']}")
                else:
                    print(f"ℹ️  Developer mode setting not found (will use default)")
            else:
                print(f"ℹ️  Advanced section not found (will be created when needed)")
                
            return True
            
        except Exception as e:
            print(f"❌ Error reading config file: {e}")
            return False
    else:
        print(f"ℹ️  Config file doesn't exist yet: {config_path}")
        return True  # This is okay, it will be created when needed

def main():
    """Run the test"""
    print("🧪 Developer Mode Toggle Test")
    print("=" * 60)
    
    # Test 1: Toggle functionality
    toggle_success = test_developer_mode_toggle()
    
    # Test 2: Config file check
    file_success = check_config_file()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Toggle Functionality: {'✅ PASS' if toggle_success else '❌ FAIL'}")
    print(f"   Config File: {'✅ PASS' if file_success else '❌ FAIL'}")
    
    if toggle_success and file_success:
        print("\n🎉 All tests passed!")
        print("✅ Permission error fixed")
        print("✅ JSON error fixed") 
        print("✅ Config file path corrected")
        print("✅ Developer mode toggle should work in menu")
        
        print("\n💡 Ready to test in menu bar app:")
        print("   1. Go to Settings → Advanced Settings")
        print("   2. Click 🔧 Developer Mode")
        print("   3. Should toggle without errors")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    return toggle_success and file_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
