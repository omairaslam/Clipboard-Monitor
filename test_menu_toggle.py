#!/usr/bin/env python3
"""
Test the menu bar app's developer mode toggle functionality
"""

import sys
import os
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_menu_toggle_functionality():
    """Test that the menu bar app can toggle developer mode without errors"""
    print("🔧 Testing Menu Bar App Toggle Functionality")
    print("=" * 60)
    
    try:
        from menu_bar_app import ClipboardMonitorMenuBar
        from config_manager import ConfigManager
        import rumps
        
        print("📋 Step 1: Create minimal menu bar app instance")
        
        # Create a minimal instance for testing
        app = ClipboardMonitorMenuBar.__new__(ClipboardMonitorMenuBar)
        
        # Initialize required attributes
        app.config_manager = ConfigManager()
        app.developer_mode = app.config_manager.get_config_value('advanced', 'developer_mode', False)
        app.developer_mode_item = rumps.MenuItem("🔧 Developer Mode", callback=app.toggle_developer_mode)
        app.developer_mode_item.state = app.developer_mode
        
        print(f"   ✅ Instance created")
        print(f"   Current developer mode: {app.developer_mode}")
        
        print("\n📋 Step 2: Test set_config_and_reload method")
        
        # Test the set_config_and_reload method directly
        original_value = app.developer_mode
        new_value = not original_value
        
        success = app.set_config_and_reload('advanced', 'developer_mode', new_value)
        print(f"   Set to {new_value}: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        if success:
            # Check if config manager was reloaded
            reloaded_value = app.config_manager.get_config_value('advanced', 'developer_mode', False)
            print(f"   Reloaded value: {reloaded_value}")
            print(f"   Match expected: {'✅ YES' if reloaded_value == new_value else '❌ NO'}")
            
            # Reset to original value
            app.set_config_and_reload('advanced', 'developer_mode', original_value)
            print(f"   Reset to original: {original_value}")
            
            return success and (reloaded_value == new_value)
        
        return False
        
    except Exception as e:
        print(f"❌ Menu toggle test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_config_file_updates():
    """Check that config file is being updated correctly"""
    print("\n📁 Checking Config File Updates")
    print("=" * 60)
    
    config_path = Path.home() / "Library" / "Application Support" / "ClipboardMonitor" / "config.json"
    
    try:
        from utils import set_config_value
        import json
        
        print("📋 Step 1: Record current state")
        if config_path.exists():
            with open(config_path, 'r') as f:
                before_config = json.load(f)
            before_value = before_config.get('advanced', {}).get('developer_mode', False)
        else:
            before_value = False
        
        print(f"   Before: {before_value}")
        
        print("\n📋 Step 2: Update config")
        new_value = not before_value
        success = set_config_value('advanced', 'developer_mode', new_value)
        print(f"   Set to {new_value}: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        if success:
            print("\n📋 Step 3: Verify file was updated")
            with open(config_path, 'r') as f:
                after_config = json.load(f)
            after_value = after_config.get('advanced', {}).get('developer_mode', False)
            
            print(f"   After: {after_value}")
            print(f"   File updated: {'✅ YES' if after_value == new_value else '❌ NO'}")
            
            # Reset to original
            set_config_value('advanced', 'developer_mode', before_value)
            print(f"   Reset to: {before_value}")
            
            return after_value == new_value
        
        return False
        
    except Exception as e:
        print(f"❌ Config file update test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Menu Bar App Developer Mode Toggle Test")
    print("=" * 70)
    
    # Test 1: Menu toggle functionality
    menu_success = test_menu_toggle_functionality()
    
    # Test 2: Config file updates
    file_success = check_config_file_updates()
    
    print("\n" + "=" * 70)
    print("📊 Test Results:")
    print(f"   Menu Toggle: {'✅ PASS' if menu_success else '❌ FAIL'}")
    print(f"   Config File: {'✅ PASS' if file_success else '❌ FAIL'}")
    
    if menu_success and file_success:
        print("\n🎉 All tests passed!")
        print("✅ Menu bar app can toggle developer mode without errors")
        print("✅ Config file is updated correctly")
        print("✅ Config manager reload works properly")
        print("✅ No permission or JSON errors")
        
        print("\n🚀 Ready for production use!")
        print("   The developer mode toggle in the menu should work perfectly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    return menu_success and file_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
