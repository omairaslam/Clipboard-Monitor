#!/usr/bin/env python3
"""
Integration test to verify the application components work correctly
with the tilde expansion fix.
"""

import os
import sys
import tempfile
import json
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_history_module():
    """Test that the history module works correctly"""
    print("🧪 Testing history module...")
    
    try:
        from modules.history_module import get_history_path, load_history, add_to_history
        
        # Test path expansion
        history_path = get_history_path()
        print(f"  History path: {history_path}")
        
        if "~" in history_path:
            print("  ❌ History path contains literal ~")
            return False
        
        if not os.path.isabs(history_path):
            print("  ❌ History path is not absolute")
            return False
            
        print("  ✅ History path properly expanded")
        
        # Test loading history (should not create ~ folder)
        original_cwd = os.getcwd()
        try:
            # Change to a temp directory to test
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                
                # Try to load history
                history = load_history()
                print(f"  Loaded {len(history)} history items")
                
                # Check no ~ folder was created
                if os.path.exists("~"):
                    print("  ❌ Literal ~ folder was created!")
                    return False
                else:
                    print("  ✅ No literal ~ folder created")
                    
        finally:
            os.chdir(original_cwd)
            
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing history module: {e}")
        return False

def test_main_module():
    """Test that the main module works correctly"""
    print("\n🧪 Testing main module...")
    
    try:
        from main import ClipboardMonitor
        
        # Test creating monitor instance
        monitor = ClipboardMonitor()
        print("  ✅ ClipboardMonitor instance created successfully")
        
        # Test module config loading
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                
                # Try to load module config
                config = monitor._load_module_config()
                print(f"  Module config loaded: {type(config)}")
                
                # Check no ~ folder was created
                if os.path.exists("~"):
                    print("  ❌ Literal ~ folder was created!")
                    return False
                else:
                    print("  ✅ No literal ~ folder created")
                    
        finally:
            os.chdir(original_cwd)
            
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing main module: {e}")
        return False

def test_cli_history_viewer():
    """Test that the CLI history viewer works correctly"""
    print("\n🧪 Testing CLI history viewer...")
    
    try:
        from cli_history_viewer import load_history
        
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                
                # Try to load history
                history = load_history()
                print(f"  CLI loaded {len(history)} history items")
                
                # Check no ~ folder was created
                if os.path.exists("~"):
                    print("  ❌ Literal ~ folder was created!")
                    return False
                else:
                    print("  ✅ No literal ~ folder created")
                    
        finally:
            os.chdir(original_cwd)
            
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing CLI history viewer: {e}")
        return False

def test_web_history_viewer():
    """Test that the web history viewer works correctly"""
    print("\n🧪 Testing web history viewer...")
    
    try:
        from web_history_viewer import create_html_viewer
        
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                
                # Try to create HTML viewer
                html_content = create_html_viewer()
                print(f"  HTML content generated: {len(html_content)} characters")
                
                # Check no ~ folder was created
                if os.path.exists("~"):
                    print("  ❌ Literal ~ folder was created!")
                    return False
                else:
                    print("  ✅ No literal ~ folder created")
                    
        finally:
            os.chdir(original_cwd)
            
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing web history viewer: {e}")
        return False

def test_menu_bar_app_imports():
    """Test that menu bar app imports work correctly"""
    print("\n🧪 Testing menu bar app imports...")
    
    try:
        # Test importing the utilities
        from utils import safe_expanduser, ensure_directory_exists
        print("  ✅ Utils imported successfully")
        
        # Test that the menu bar app can import these
        # Note: We can't fully test the menu bar app without rumps GUI
        # but we can test the import and basic path operations
        
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                
                # Test the path operations that the menu bar app uses
                test_paths = [
                    "~/Library/Application Support/ClipboardMonitor/pause_flag",
                    "~/Library/Application Support/ClipboardMonitor/config.json",
                    "~/Library/Application Support/ClipboardMonitor/clipboard_history.json"
                ]
                
                for path in test_paths:
                    expanded = safe_expanduser(path)
                    if "~" in expanded:
                        print(f"  ❌ Path still contains ~: {path} -> {expanded}")
                        return False
                
                print("  ✅ All menu bar app paths expand correctly")
                
                # Check no ~ folder was created
                if os.path.exists("~"):
                    print("  ❌ Literal ~ folder was created!")
                    return False
                else:
                    print("  ✅ No literal ~ folder created")
                    
        finally:
            os.chdir(original_cwd)
            
        return True
        
    except Exception as e:
        print(f"  ❌ Error testing menu bar app: {e}")
        return False

def test_plist_environment():
    """Test that plist files have correct environment setup"""
    print("\n🧪 Testing plist environment configuration...")
    
    plist_files = [
        "com.omairaslam.clipboardmonitor.plist",
        "com.omairaslam.clipboardmonitor.menubar.plist"
    ]
    
    all_passed = True
    
    for plist_file in plist_files:
        if os.path.exists(plist_file):
            try:
                with open(plist_file, 'r') as f:
                    content = f.read()
                    
                print(f"  Checking {plist_file}...")
                
                # Check that HOME environment variable is set
                if "<key>HOME</key>" in content:
                    print(f"    ✅ HOME environment variable is set")
                else:
                    print(f"    ❌ HOME environment variable is missing")
                    all_passed = False
                    
                # Check that it's set to the correct path
                if "/Users/omair.aslam" in content:
                    print(f"    ✅ HOME path is correctly set")
                else:
                    print(f"    ❌ HOME path may be incorrect")
                    all_passed = False
                    
            except Exception as e:
                print(f"    ❌ Error reading {plist_file}: {e}")
                all_passed = False
        else:
            print(f"  ⚠️  {plist_file} not found (may be normal)")
    
    return all_passed

def main():
    """Run all integration tests"""
    print("🔧 Testing Application Integration with Tilde Fix")
    print("=" * 60)
    
    tests = [
        ("History Module", test_history_module),
        ("Main Module", test_main_module),
        ("CLI History Viewer", test_cli_history_viewer),
        ("Web History Viewer", test_web_history_viewer),
        ("Menu Bar App Imports", test_menu_bar_app_imports),
        ("Plist Environment", test_plist_environment)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        if test_func():
            print(f"✅ {test_name} PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 60)
    print(f"📊 Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! The application is ready.")
        return True
    else:
        print("⚠️  Some integration tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
