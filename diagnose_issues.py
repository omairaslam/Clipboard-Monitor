#!/usr/bin/env python3
"""
Diagnose the current issues with modules and developer mode
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def check_config_system():
    """Check if the config system is working"""
    print("🔍 Checking Config System")
    print("=" * 30)
    
    try:
        from utils import get_config, set_config_value
        
        # Test basic config operations
        test_value = get_config('test', 'diagnostic', 'default')
        print(f"✅ Config read test: {test_value}")
        
        success = set_config_value('test', 'diagnostic', 'working')
        print(f"✅ Config write test: {'SUCCESS' if success else 'FAILED'}")
        
        if success:
            verify_value = get_config('test', 'diagnostic', 'default')
            print(f"✅ Config verify test: {verify_value}")
            
            # Clean up
            set_config_value('test', 'diagnostic', None)
        
        return success
        
    except Exception as e:
        print(f"❌ Config system error: {e}")
        return False

def check_module_config():
    """Check the module configuration"""
    print("\n🧩 Checking Module Configuration")
    print("=" * 35)
    
    try:
        from utils import get_config
        
        # Check if modules section exists
        modules_config = get_config('modules', default={})
        print(f"✅ Modules config: {modules_config}")
        
        if not modules_config:
            print("ℹ️  No modules config found - all modules will appear enabled by default")
        
        # Check specific modules
        test_modules = ['markdown_module', 'mermaid_module', 'drawio_module', 'history_module']
        for module in test_modules:
            status = get_config('modules', module, True)  # Default True
            print(f"   {module}: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Module config error: {e}")
        return False

def check_developer_mode():
    """Check developer mode configuration"""
    print("\n🔧 Checking Developer Mode")
    print("=" * 30)
    
    try:
        from utils import get_config, set_config_value
        
        # Check current developer mode
        current_mode = get_config('advanced', 'developer_mode', False)
        print(f"✅ Current developer mode: {current_mode}")
        
        # Test toggling
        new_mode = not current_mode
        success = set_config_value('advanced', 'developer_mode', new_mode)
        print(f"✅ Toggle test: {'SUCCESS' if success else 'FAILED'}")
        
        if success:
            verify_mode = get_config('advanced', 'developer_mode', False)
            print(f"✅ Verify toggle: {verify_mode}")
            
            # Reset to original
            set_config_value('advanced', 'developer_mode', current_mode)
            print(f"✅ Reset to original: {current_mode}")
        
        return success
        
    except Exception as e:
        print(f"❌ Developer mode error: {e}")
        return False

def check_config_file():
    """Check the actual config file"""
    print("\n📁 Checking Config File")
    print("=" * 25)
    
    try:
        config_path = Path.home() / "Library" / "Application Support" / "ClipboardMonitor" / "config.json"
        
        if config_path.exists():
            print(f"✅ Config file exists: {config_path}")
            
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            print(f"✅ Config sections: {list(config.keys())}")
            
            if 'modules' in config:
                print(f"✅ Modules section: {config['modules']}")
            else:
                print(f"ℹ️  No modules section in config")
            
            if 'advanced' in config:
                print(f"✅ Advanced section: {config['advanced']}")
            else:
                print(f"ℹ️  No advanced section in config")
            
            return True
        else:
            print(f"❌ Config file not found: {config_path}")
            return False
            
    except Exception as e:
        print(f"❌ Config file error: {e}")
        return False

def check_running_instance():
    """Check if the menu bar app is running"""
    print("\n🖥️  Checking Running Instance")
    print("=" * 30)
    
    try:
        import subprocess
        
        result = subprocess.run(['pgrep', '-f', 'menu_bar_app.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            pid = result.stdout.strip()
            print(f"✅ Menu bar app running (PID: {pid})")
            return True
        else:
            print(f"❌ Menu bar app not running")
            return False
            
    except Exception as e:
        print(f"❌ Instance check error: {e}")
        return False

def main():
    """Run all diagnostic checks"""
    print("🩺 Diagnosing Clipboard Monitor Issues")
    print("=" * 45)
    
    # Run all checks
    config_ok = check_config_system()
    module_ok = check_module_config()
    dev_mode_ok = check_developer_mode()
    file_ok = check_config_file()
    instance_ok = check_running_instance()
    
    print("\n" + "=" * 45)
    print("📊 Diagnostic Results:")
    print(f"   Config System: {'✅ OK' if config_ok else '❌ BROKEN'}")
    print(f"   Module Config: {'✅ OK' if module_ok else '❌ BROKEN'}")
    print(f"   Developer Mode: {'✅ OK' if dev_mode_ok else '❌ BROKEN'}")
    print(f"   Config File: {'✅ OK' if file_ok else '❌ BROKEN'}")
    print(f"   Running Instance: {'✅ OK' if instance_ok else '❌ BROKEN'}")
    
    if all([config_ok, module_ok, dev_mode_ok, file_ok, instance_ok]):
        print("\n🎉 All systems appear to be working!")
        print("   The issues might be in the menu building logic.")
    else:
        print("\n⚠️  Found issues that need to be fixed:")
        if not config_ok:
            print("   - Config system is broken")
        if not module_ok:
            print("   - Module configuration is broken")
        if not dev_mode_ok:
            print("   - Developer mode toggle is broken")
        if not file_ok:
            print("   - Config file is missing or corrupted")
        if not instance_ok:
            print("   - Menu bar app is not running")
    
    return all([config_ok, module_ok, dev_mode_ok, file_ok, instance_ok])

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
