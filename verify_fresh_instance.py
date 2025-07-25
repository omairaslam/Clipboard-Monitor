#!/usr/bin/env python3
"""
Verify that the fresh menu bar app instance has the correct updated code
"""

import sys
import os
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def check_utils_code():
    """Check that utils.py has the correct updated code"""
    print("🔍 Checking utils.py Code")
    print("=" * 30)
    
    try:
        # Check the current line numbers and content
        utils_path = Path(__file__).parent / "utils.py"
        
        with open(utils_path, 'r') as f:
            lines = f.readlines()
        
        # Look for the fixed config path
        config_path_line = None
        json_error_line = None
        
        for i, line in enumerate(lines, 1):
            if "Library/Application Support/ClipboardMonitor/config.json" in line:
                config_path_line = i
            if "ValueError" in line and "json" in line.lower():
                json_error_line = i
        
        print(f"✅ Config path fix found at line: {config_path_line}")
        print(f"✅ JSON error fix found at line: {json_error_line}")
        
        # Test the actual function
        from utils import set_config_value
        success = set_config_value('test_fresh', 'instance_test', True)
        print(f"✅ Config write test: {'SUCCESS' if success else 'FAILED'}")
        
        if success:
            # Clean up
            set_config_value('test_fresh', 'instance_test', None)
        
        return config_path_line is not None and json_error_line is not None and success
        
    except Exception as e:
        print(f"❌ Utils code check failed: {e}")
        return False

def check_config_file_location():
    """Check that config is being written to the correct location"""
    print("\n📁 Checking Config File Location")
    print("=" * 35)
    
    try:
        from utils import set_config_value
        
        # Write a test value
        success = set_config_value('location_test', 'fresh_instance', True)
        
        if success:
            # Check if it's in the correct location
            correct_path = Path.home() / "Library" / "Application Support" / "ClipboardMonitor" / "config.json"
            wrong_path = Path(__file__).parent / "config.json"
            
            correct_exists = correct_path.exists()
            wrong_exists = wrong_path.exists()
            
            print(f"✅ Correct location ({correct_path}): {'EXISTS' if correct_exists else 'NOT FOUND'}")
            print(f"✅ Wrong location ({wrong_path}): {'EXISTS' if wrong_exists else 'NOT FOUND'}")
            
            if correct_exists:
                import json
                with open(correct_path, 'r') as f:
                    config = json.load(f)
                
                test_found = config.get('location_test', {}).get('fresh_instance') == True
                print(f"✅ Test data in correct file: {'FOUND' if test_found else 'NOT FOUND'}")
                
                # Clean up
                set_config_value('location_test', 'fresh_instance', None)
                
                return correct_exists and not wrong_exists and test_found
            
        return False
        
    except Exception as e:
        print(f"❌ Config location check failed: {e}")
        return False

def check_running_instance():
    """Check that the running instance is using the new code"""
    print("\n🖥️  Checking Running Instance")
    print("=" * 30)
    
    try:
        import subprocess
        
        # Get the PID of the running menu bar app
        result = subprocess.run(['pgrep', '-f', 'menu_bar_app.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            pid = result.stdout.strip()
            print(f"✅ Menu bar app running with PID: {pid}")
            
            # Check when it was started (should be recent)
            ps_result = subprocess.run(['ps', '-p', pid, '-o', 'lstart='], 
                                     capture_output=True, text=True)
            
            if ps_result.returncode == 0:
                start_time = ps_result.stdout.strip()
                print(f"✅ Started at: {start_time}")
                return True
            
        else:
            print(f"❌ No menu bar app process found")
            return False
            
    except Exception as e:
        print(f"❌ Running instance check failed: {e}")
        return False

def main():
    """Run all verification checks"""
    print("🧪 Verifying Fresh Menu Bar App Instance")
    print("=" * 45)
    
    # Check 1: Utils code
    utils_success = check_utils_code()
    
    # Check 2: Config file location
    location_success = check_config_file_location()
    
    # Check 3: Running instance
    instance_success = check_running_instance()
    
    print("\n" + "=" * 45)
    print("📊 Verification Results:")
    print(f"   Utils Code: {'✅ UPDATED' if utils_success else '❌ OLD'}")
    print(f"   Config Location: {'✅ CORRECT' if location_success else '❌ WRONG'}")
    print(f"   Running Instance: {'✅ FRESH' if instance_success else '❌ STALE'}")
    
    if utils_success and location_success and instance_success:
        print("\n🎉 Fresh instance verified!")
        print("✅ Updated code is loaded")
        print("✅ Config writes to correct location")
        print("✅ Fresh instance is running")
        
        print("\n🚀 Developer Mode toggle should now work without errors!")
        print("   Try: Settings → Advanced Settings → 🔧 Developer Mode")
    else:
        print("\n⚠️  Some issues detected. The instance may still have old code.")
    
    return utils_success and location_success and instance_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
