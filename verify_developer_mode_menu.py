#!/usr/bin/env python3
"""
Verification script to check if developer mode menu structure is correct
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def verify_menu_structure():
    """Verify that the menu structure includes Advanced Settings with Developer Mode"""
    print("🔍 Verifying Menu Structure")
    print("=" * 50)
    
    try:
        from menu_bar_app import ClipboardMonitorMenuBar
        
        # Create a minimal instance to test menu structure
        app = ClipboardMonitorMenuBar.__new__(ClipboardMonitorMenuBar)
        
        # Initialize minimal required attributes
        from config_manager import ConfigManager
        app.config_manager = ConfigManager()
        app.developer_mode = False
        
        # Mock required attributes for menu creation
        import rumps
        app.developer_mode_item = rumps.MenuItem("🔧 Developer Mode")
        
        # Test the advanced settings menu creation
        try:
            advanced_menu = app._create_advanced_settings_menu()
            print(f"✅ Advanced Settings menu created successfully")
            print(f"   Menu title: {advanced_menu.title}")
            
            # Check if developer mode item is in the menu
            has_developer_mode = False
            for item in advanced_menu._menu:
                if hasattr(item, 'title') and 'Developer Mode' in item.title:
                    has_developer_mode = True
                    print(f"✅ Developer Mode toggle found: {item.title}")
                    break
            
            if not has_developer_mode:
                print(f"❌ Developer Mode toggle not found in Advanced Settings")
                return False
                
        except Exception as e:
            print(f"❌ Failed to create Advanced Settings menu: {e}")
            return False
        
        # Test the clean settings menu creation
        try:
            settings_menu = app._create_clean_settings_menu()
            print(f"✅ Settings menu created successfully")
            print(f"   Menu title: {settings_menu.title}")
            
            # Check if advanced settings is included
            has_advanced_settings = False
            for item in settings_menu._menu:
                if hasattr(item, 'title') and 'Advanced Settings' in item.title:
                    has_advanced_settings = True
                    print(f"✅ Advanced Settings submenu found: {item.title}")
                    break
            
            if not has_advanced_settings:
                print(f"❌ Advanced Settings submenu not found in Settings menu")
                return False
                
        except Exception as e:
            print(f"❌ Failed to create Settings menu: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Menu structure verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_current_developer_mode():
    """Check the current developer mode setting"""
    print("\n🔧 Checking Current Developer Mode Setting")
    print("=" * 50)
    
    try:
        from config_manager import ConfigManager
        config_manager = ConfigManager()
        
        current_mode = config_manager.get_config_value('advanced', 'developer_mode', False)
        print(f"✅ Current developer mode: {current_mode}")
        print(f"   Expected behavior: {'Show memory/CPU data and dashboard' if current_mode else 'Clean end-user interface'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to check developer mode setting: {e}")
        return False

def main():
    """Run verification"""
    print("🧪 Developer Mode Menu Verification")
    print("=" * 60)
    
    # Test 1: Menu Structure
    menu_success = verify_menu_structure()
    
    # Test 2: Current Setting
    setting_success = check_current_developer_mode()
    
    print("\n" + "=" * 60)
    print("📊 Verification Results:")
    print(f"   Menu Structure: {'✅ PASS' if menu_success else '❌ FAIL'}")
    print(f"   Current Setting: {'✅ PASS' if setting_success else '❌ FAIL'}")
    
    if menu_success and setting_success:
        print("\n🎉 Verification successful!")
        print("\n📋 How to Access Developer Mode:")
        print("   1. Click on the Clipboard Monitor menu bar icon")
        print("   2. Navigate to: ⚙️ Settings → Advanced Settings")
        print("   3. Look for: 🔧 Developer Mode")
        print("   4. Click to toggle between End User and Developer modes")
        print("\n💡 Expected Behavior:")
        print("   • End User Mode: Clean interface, no memory data")
        print("   • Developer Mode: Shows memory/CPU stats and dashboard")
    else:
        print("\n⚠️  Verification failed. Check the output above for details.")
    
    return menu_success and setting_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
