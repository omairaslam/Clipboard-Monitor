#!/usr/bin/env python3
"""
Test script to verify the tilde expansion fix works correctly.
This script tests the robust path utility functions to ensure they prevent
the creation of literal ~ folders.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add current directory to path to import utils
sys.path.insert(0, os.path.dirname(__file__))
from utils import safe_expanduser, get_home_directory, ensure_directory_exists

def test_get_home_directory():
    """Test that get_home_directory returns a valid home directory"""
    print("🧪 Testing get_home_directory()...")
    
    try:
        home_dir = get_home_directory()
        print(f"✅ Home directory found: {home_dir}")
        
        # Verify it's a valid directory
        if os.path.isdir(home_dir):
            print("✅ Home directory exists and is a directory")
        else:
            print("❌ Home directory path is not a valid directory")
            return False
            
        # Verify it doesn't contain literal ~
        if "~" in home_dir:
            print("❌ Home directory contains literal ~ character")
            return False
        else:
            print("✅ Home directory does not contain literal ~ character")
            
        return True
        
    except Exception as e:
        print(f"❌ Error getting home directory: {e}")
        return False

def test_safe_expanduser():
    """Test that safe_expanduser properly expands paths"""
    print("\n🧪 Testing safe_expanduser()...")
    
    test_cases = [
        "~/test/path",
        "~/Library/Application Support/ClipboardMonitor",
        "~",
        "/absolute/path",
        "relative/path"
    ]
    
    all_passed = True
    
    for test_path in test_cases:
        try:
            expanded = safe_expanduser(test_path)
            print(f"  Input: {test_path}")
            print(f"  Output: {expanded}")
            
            # Check that ~ paths are properly expanded
            if test_path.startswith("~"):
                if "~" in expanded:
                    print(f"  ❌ Still contains ~ character: {expanded}")
                    all_passed = False
                elif not os.path.isabs(expanded):
                    print(f"  ❌ Not an absolute path: {expanded}")
                    all_passed = False
                else:
                    print(f"  ✅ Properly expanded to absolute path")
            else:
                # Non-~ paths should be unchanged
                if expanded == test_path:
                    print(f"  ✅ Non-~ path unchanged")
                else:
                    print(f"  ❌ Non-~ path was modified unexpectedly")
                    all_passed = False
                    
        except Exception as e:
            print(f"  ❌ Error expanding {test_path}: {e}")
            all_passed = False
            
        print()
    
    return all_passed

def test_ensure_directory_exists():
    """Test that ensure_directory_exists works with ~ paths"""
    print("🧪 Testing ensure_directory_exists()...")
    
    # Create a temporary test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with a ~ path (simulated)
        test_path = os.path.join(temp_dir, "test_dir")
        
        try:
            result = ensure_directory_exists(test_path)
            
            if result and os.path.isdir(test_path):
                print(f"✅ Directory created successfully: {test_path}")
                return True
            else:
                print(f"❌ Failed to create directory: {test_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating directory: {e}")
            return False

def test_working_directory_independence():
    """Test that our functions work regardless of current working directory"""
    print("\n🧪 Testing working directory independence...")
    
    original_cwd = os.getcwd()
    
    try:
        # Change to a different directory
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            print(f"  Changed working directory to: {temp_dir}")
            
            # Test that our functions still work correctly
            home_dir = get_home_directory()
            expanded_path = safe_expanduser("~/test")
            
            # Verify results are still correct
            if os.path.isabs(home_dir) and not "~" in home_dir:
                print("  ✅ get_home_directory() works from different working directory")
            else:
                print("  ❌ get_home_directory() failed from different working directory")
                return False
                
            if os.path.isabs(expanded_path) and not "~" in expanded_path:
                print("  ✅ safe_expanduser() works from different working directory")
            else:
                print("  ❌ safe_expanduser() failed from different working directory")
                return False
                
            return True
            
    except Exception as e:
        print(f"  ❌ Error testing working directory independence: {e}")
        return False
    finally:
        # Always restore original working directory
        os.chdir(original_cwd)

def test_no_literal_tilde_creation():
    """Test that no literal ~ directories are created"""
    print("\n🧪 Testing that no literal ~ directories are created...")
    
    original_cwd = os.getcwd()
    
    try:
        # Create a temporary directory to test in
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            print(f"  Testing in temporary directory: {temp_dir}")
            
            # Try operations that might create ~ directories
            test_paths = [
                "~/Library/Application Support/ClipboardMonitor/test.json",
                "~/test_file.txt"
            ]
            
            for test_path in test_paths:
                try:
                    expanded = safe_expanduser(test_path)
                    
                    # Create the directory structure
                    dir_path = os.path.dirname(expanded)
                    ensure_directory_exists(dir_path)
                    
                    print(f"    Tested path: {test_path} -> {expanded}")
                    
                except Exception as e:
                    print(f"    ❌ Error with path {test_path}: {e}")
                    return False
            
            # Check that no ~ directory was created in the temp directory
            if os.path.exists(os.path.join(temp_dir, "~")):
                print("  ❌ Literal ~ directory was created!")
                return False
            else:
                print("  ✅ No literal ~ directory created")
                
            return True
            
    except Exception as e:
        print(f"  ❌ Error in literal tilde test: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def test_real_application_paths():
    """Test the actual paths used by the application"""
    print("\n🧪 Testing real application paths...")
    
    app_paths = [
        "~/Library/Application Support/ClipboardMonitor/clipboard_history.json",
        "~/Library/Application Support/ClipboardMonitor/config.json",
        "~/Library/Application Support/ClipboardMonitor/pause_flag",
        "~/Library/Application Support/ClipboardMonitor/modules_config.json"
    ]
    
    all_passed = True
    
    for path in app_paths:
        try:
            expanded = safe_expanduser(path)
            print(f"  {path}")
            print(f"    -> {expanded}")
            
            # Verify it's absolute and doesn't contain ~
            if not os.path.isabs(expanded):
                print(f"    ❌ Not absolute path")
                all_passed = False
            elif "~" in expanded:
                print(f"    ❌ Contains literal ~")
                all_passed = False
            else:
                print(f"    ✅ Properly expanded")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests"""
    print("🔧 Testing Tilde Expansion Fix")
    print("=" * 50)
    
    tests = [
        ("Home Directory Detection", test_get_home_directory),
        ("Safe Expanduser Function", test_safe_expanduser),
        ("Directory Creation", test_ensure_directory_exists),
        ("Working Directory Independence", test_working_directory_independence),
        ("No Literal Tilde Creation", test_no_literal_tilde_creation),
        ("Real Application Paths", test_real_application_paths)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        if test_func():
            print(f"✅ {test_name} PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The tilde expansion fix is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
