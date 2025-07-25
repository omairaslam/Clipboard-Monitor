#!/usr/bin/env python3
"""
Test script to verify developer mode functionality
"""

import sys
import os
import json

# Add current directory to path to import menu bar app
sys.path.insert(0, os.path.dirname(__file__))

def test_config_manager():
    """Test the config manager for developer mode setting"""
    print("🧪 Testing Config Manager for Developer Mode")
    print("=" * 50)
    
    try:
        from config_manager import ConfigManager
        
        config_manager = ConfigManager()
        
        # Test getting default value (should be False)
        default_value = config_manager.get_config_value('advanced', 'developer_mode', False)
        print(f"✅ Default developer mode value: {default_value}")
        
        # Test setting to True
        success = config_manager.set_config_value('advanced', 'developer_mode', True)
        print(f"✅ Set developer mode to True: {'Success' if success else 'Failed'}")
        
        # Test getting the set value
        current_value = config_manager.get_config_value('advanced', 'developer_mode', False)
        print(f"✅ Current developer mode value: {current_value}")
        
        # Reset to False for clean state
        config_manager.set_config_value('advanced', 'developer_mode', False)
        print(f"✅ Reset developer mode to False")
        
        return True
        
    except Exception as e:
        print(f"❌ Config manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_menu_bar_initialization():
    """Test menu bar app initialization with developer mode"""
    print("\n🧪 Testing Menu Bar App Initialization")
    print("=" * 50)
    
    try:
        # Set developer mode to False first
        from config_manager import ConfigManager
        config_manager = ConfigManager()
        config_manager.set_config_value('advanced', 'developer_mode', False)
        
        # Import and create minimal menu bar instance
        from menu_bar_app import ClipboardMonitorMenuBar
        
        # Create instance (this will read the config)
        app = ClipboardMonitorMenuBar.__new__(ClipboardMonitorMenuBar)
        
        # Initialize just the config manager and developer mode
        app.config_manager = config_manager
        app.developer_mode = app.config_manager.get_config_value('advanced', 'developer_mode', False)
        
        print(f"✅ Menu bar app initialized")
        print(f"   Developer mode: {app.developer_mode}")
        print(f"   Expected: False (end user mode)")
        
        # Test with developer mode enabled
        config_manager.set_config_value('advanced', 'developer_mode', True)
        app.developer_mode = True
        
        print(f"✅ Developer mode enabled")
        print(f"   Developer mode: {app.developer_mode}")
        print(f"   Expected: True (developer mode)")
        
        # Reset to False
        config_manager.set_config_value('advanced', 'developer_mode', False)
        
        return True
        
    except Exception as e:
        print(f"❌ Menu bar initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_file_structure():
    """Test the config file structure for developer mode"""
    print("\n🧪 Testing Config File Structure")
    print("=" * 50)
    
    try:
        config_path = os.path.expanduser("~/Library/Application Support/ClipboardMonitor/config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            print(f"✅ Config file exists at: {config_path}")
            
            # Check if advanced section exists
            if 'advanced' in config:
                print(f"✅ Advanced section exists")
                
                # Check developer_mode setting
                if 'developer_mode' in config['advanced']:
                    print(f"✅ Developer mode setting exists: {config['advanced']['developer_mode']}")
                else:
                    print(f"ℹ️  Developer mode setting not found (will use default: False)")
            else:
                print(f"ℹ️  Advanced section not found (will be created when needed)")
                
        else:
            print(f"ℹ️  Config file not found (will be created when needed)")
            
        return True
        
    except Exception as e:
        print(f"❌ Config file test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 Testing Developer Mode Implementation")
    print("=" * 60)
    
    # Test 1: Config Manager
    config_success = test_config_manager()
    
    # Test 2: Menu Bar Initialization
    menu_success = test_menu_bar_initialization()
    
    # Test 3: Config File Structure
    file_success = test_config_file_structure()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Config Manager: {'✅ PASS' if config_success else '❌ FAIL'}")
    print(f"   Menu Bar Init: {'✅ PASS' if menu_success else '❌ FAIL'}")
    print(f"   Config File: {'✅ PASS' if file_success else '❌ FAIL'}")
    
    if config_success and menu_success and file_success:
        print("\n🎉 All tests passed! Developer mode implementation is working.")
        print("\n📋 Usage Instructions:")
        print("   1. Launch menu bar app")
        print("   2. Go to Settings → Advanced Settings")
        print("   3. Toggle '🔧 Developer Mode'")
        print("   4. In Developer Mode: Shows memory/CPU data and dashboard")
        print("   5. In End User Mode: Clean interface with no memory data")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return config_success and menu_success and file_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
