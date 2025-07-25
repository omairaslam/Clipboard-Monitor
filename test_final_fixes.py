#!/usr/bin/env python3
"""
Test that the final fixes work correctly
"""

import sys
import os
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_developer_mode_toggle():
    """Test that developer mode toggle works"""
    print("🔧 Testing Developer Mode Toggle")
    print("=" * 35)
    
    try:
        from utils import get_config, set_config_value
        
        # Get current state
        current_mode = get_config('advanced', 'developer_mode', False)
        print(f"✅ Current developer mode: {current_mode}")
        
        # Toggle to opposite
        new_mode = not current_mode
        success = set_config_value('advanced', 'developer_mode', new_mode)
        print(f"✅ Toggle to {new_mode}: {'SUCCESS' if success else 'FAILED'}")
        
        if success:
            # Wait a moment for menu rebuild
            time.sleep(2)
            
            # Check if app is still running
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'menu_bar_app.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ App still running after toggle")
                
                # Toggle back
                reset_success = set_config_value('advanced', 'developer_mode', current_mode)
                print(f"✅ Reset to {current_mode}: {'SUCCESS' if reset_success else 'FAILED'}")
                
                return success and reset_success
            else:
                print(f"❌ App crashed during toggle")
                return False
        
        return False
        
    except Exception as e:
        print(f"❌ Developer mode toggle test failed: {e}")
        return False

def test_module_toggle():
    """Test that module toggling works"""
    print("\n🧩 Testing Module Toggle")
    print("=" * 25)
    
    try:
        from utils import get_config, set_config_value
        
        # Test toggling a specific module
        test_module = 'code_formatter_module'
        current_state = get_config('modules', test_module, True)
        print(f"✅ Current {test_module}: {current_state}")
        
        # Toggle it
        new_state = not current_state
        success = set_config_value('modules', test_module, new_state)
        print(f"✅ Toggle to {new_state}: {'SUCCESS' if success else 'FAILED'}")
        
        if success:
            # Verify the change
            verify_state = get_config('modules', test_module, True)
            print(f"✅ Verified state: {verify_state}")
            
            # Reset to original
            reset_success = set_config_value('modules', test_module, current_state)
            print(f"✅ Reset to {current_state}: {'SUCCESS' if reset_success else 'FAILED'}")
            
            return success and (verify_state == new_state) and reset_success
        
        return False
        
    except Exception as e:
        print(f"❌ Module toggle test failed: {e}")
        return False

def test_config_consistency():
    """Test that config is consistent between ConfigManager and utils"""
    print("\n📊 Testing Config Consistency")
    print("=" * 30)
    
    try:
        from utils import get_config, set_config_value
        from config_manager import ConfigManager
        
        # Test with ConfigManager
        config_manager = ConfigManager()
        cm_dev_mode = config_manager.get_config_value('advanced', 'developer_mode', False)
        
        # Test with utils
        utils_dev_mode = get_config('advanced', 'developer_mode', False)
        
        print(f"✅ ConfigManager developer mode: {cm_dev_mode}")
        print(f"✅ Utils developer mode: {utils_dev_mode}")
        print(f"✅ Consistent: {cm_dev_mode == utils_dev_mode}")
        
        # Test modules
        cm_modules = config_manager.get_section('modules', {})
        utils_modules = get_config('modules', default={})
        
        print(f"✅ ConfigManager modules count: {len(cm_modules)}")
        print(f"✅ Utils modules count: {len(utils_modules)}")
        print(f"✅ Modules consistent: {cm_modules == utils_modules}")
        
        return (cm_dev_mode == utils_dev_mode) and (cm_modules == utils_modules)
        
    except Exception as e:
        print(f"❌ Config consistency test failed: {e}")
        return False

def main():
    """Run all final tests"""
    print("🧪 Testing Final Fixes")
    print("=" * 30)
    
    # Test 1: Developer mode toggle
    dev_mode_ok = test_developer_mode_toggle()
    
    # Test 2: Module toggle
    module_ok = test_module_toggle()
    
    # Test 3: Config consistency
    consistency_ok = test_config_consistency()
    
    print("\n" + "=" * 30)
    print("📊 Final Test Results:")
    print(f"   Developer Mode: {'✅ WORKS' if dev_mode_ok else '❌ BROKEN'}")
    print(f"   Module Toggle: {'✅ WORKS' if module_ok else '❌ BROKEN'}")
    print(f"   Config Consistency: {'✅ WORKS' if consistency_ok else '❌ BROKEN'}")
    
    if all([dev_mode_ok, module_ok, consistency_ok]):
        print("\n🎉 All fixes are working!")
        print("✅ Developer mode toggle works without crashing")
        print("✅ Module toggling works correctly")
        print("✅ Config system is consistent")
        
        print("\n💡 The issues should now be resolved:")
        print("   - Developer mode toggle should work in the menu")
        print("   - Module enable/disable should work properly")
        print("   - All config changes should persist correctly")
    else:
        print("\n⚠️  Some issues remain:")
        if not dev_mode_ok:
            print("   - Developer mode toggle is still broken")
        if not module_ok:
            print("   - Module toggling is still broken")
        if not consistency_ok:
            print("   - Config system has inconsistencies")
    
    return all([dev_mode_ok, module_ok, consistency_ok])

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
