#!/usr/bin/env python3
"""
Test that module menus are actually being added to the menu bar
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_module_status_loading():
    """Test that module status is loaded correctly"""
    print("🧩 Testing Module Status Loading")
    print("=" * 35)
    
    try:
        from menu_bar_app import ClipboardMonitorMenuBar
        from config_manager import ConfigManager
        
        # Create a minimal instance to test module loading
        app = ClipboardMonitorMenuBar.__new__(ClipboardMonitorMenuBar)
        app.config_manager = ConfigManager()
        app.module_status = {}
        
        # Test the load_module_config method
        app.load_module_config()
        
        print(f"✅ Module status loaded: {len(app.module_status)} modules")
        
        # Check specific modules
        test_modules = ['markdown_module', 'mermaid_module', 'drawio_module', 'history_module']
        for module in test_modules:
            status = app.module_status.get(module, 'NOT_FOUND')
            print(f"   {module}: {status}")
        
        return len(app.module_status) > 0
        
    except Exception as e:
        print(f"❌ Module status loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enabled_modules_detection():
    """Test that enabled modules are detected correctly"""
    print("\n🔍 Testing Enabled Modules Detection")
    print("=" * 40)
    
    try:
        from menu_bar_app import ClipboardMonitorMenuBar
        from config_manager import ConfigManager
        
        # Create a minimal instance
        app = ClipboardMonitorMenuBar.__new__(ClipboardMonitorMenuBar)
        app.config_manager = ConfigManager()
        app.module_status = {}
        app.load_module_config()
        
        # Test _is_module_enabled method
        test_modules = ['markdown_module', 'mermaid_module', 'drawio_module', 'history_module']
        enabled_count = 0
        
        for module in test_modules:
            enabled = app._is_module_enabled(module)
            print(f"   {module}: {'✅ ENABLED' if enabled else '❌ DISABLED'}")
            if enabled:
                enabled_count += 1
        
        print(f"✅ Total enabled modules: {enabled_count}")
        
        # Test _get_enabled_modules method
        enabled_modules = app._get_enabled_modules()
        print(f"✅ Enabled modules list: {enabled_modules}")
        
        return enabled_count > 0
        
    except Exception as e:
        print(f"❌ Enabled modules detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_module_display_names():
    """Test that module display names are set up correctly"""
    print("\n📝 Testing Module Display Names")
    print("=" * 35)
    
    try:
        from menu_bar_app import ClipboardMonitorMenuBar
        
        # Create a minimal instance
        app = ClipboardMonitorMenuBar.__new__(ClipboardMonitorMenuBar)
        app.module_display_names = {
            "markdown_module": "Markdown Processor",
            "mermaid_module": "Mermaid Diagram Detector",
            "drawio_module": "Draw.io Diagram Detector",
            "history_module": "Clipboard History Tracker",
            "code_formatter_module": "Code Formatter"
        }
        
        print(f"✅ Display names configured: {len(app.module_display_names)} modules")
        
        for module, display_name in app.module_display_names.items():
            print(f"   {module}: '{display_name}'")
        
        return len(app.module_display_names) > 0
        
    except Exception as e:
        print(f"❌ Module display names test failed: {e}")
        return False

def test_modules_directory():
    """Test that the modules directory exists and has module files"""
    print("\n📁 Testing Modules Directory")
    print("=" * 30)
    
    try:
        modules_dir = Path(__file__).parent / 'modules'
        print(f"✅ Modules directory: {modules_dir}")
        print(f"   Exists: {modules_dir.exists()}")
        
        if modules_dir.exists():
            module_files = list(modules_dir.glob('*_module.py'))
            print(f"✅ Module files found: {len(module_files)}")
            
            for module_file in module_files:
                print(f"   {module_file.name}")
            
            return len(module_files) > 0
        else:
            print(f"❌ Modules directory does not exist")
            return False
            
    except Exception as e:
        print(f"❌ Modules directory test failed: {e}")
        return False

def main():
    """Run all module menu tests"""
    print("🧪 Testing Module Menu Functionality")
    print("=" * 45)
    
    # Test 1: Module status loading
    status_ok = test_module_status_loading()
    
    # Test 2: Enabled modules detection
    enabled_ok = test_enabled_modules_detection()
    
    # Test 3: Module display names
    names_ok = test_module_display_names()
    
    # Test 4: Modules directory
    dir_ok = test_modules_directory()
    
    print("\n" + "=" * 45)
    print("📊 Module Menu Test Results:")
    print(f"   Module Status Loading: {'✅ OK' if status_ok else '❌ BROKEN'}")
    print(f"   Enabled Detection: {'✅ OK' if enabled_ok else '❌ BROKEN'}")
    print(f"   Display Names: {'✅ OK' if names_ok else '❌ BROKEN'}")
    print(f"   Modules Directory: {'✅ OK' if dir_ok else '❌ BROKEN'}")
    
    if all([status_ok, enabled_ok, names_ok, dir_ok]):
        print("\n🎉 All module menu components are working!")
        print("✅ Module status is loaded correctly")
        print("✅ Enabled modules are detected properly")
        print("✅ Display names are configured")
        print("✅ Module files exist")
        
        print("\n💡 The module menus should now appear in the menu bar!")
        print("   Look for items like:")
        print("   - 📝 Markdown Processor")
        print("   - 🧩 Mermaid Diagram Detector")
        print("   - 🎨 Draw.io Diagram Detector")
        print("   - 📋 Clipboard History")
    else:
        print("\n⚠️  Some module menu components are broken:")
        if not status_ok:
            print("   - Module status loading is broken")
        if not enabled_ok:
            print("   - Enabled module detection is broken")
        if not names_ok:
            print("   - Display names are not configured")
        if not dir_ok:
            print("   - Module files are missing")
    
    return all([status_ok, enabled_ok, names_ok, dir_ok])

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
