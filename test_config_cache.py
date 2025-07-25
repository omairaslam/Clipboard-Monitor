#!/usr/bin/env python3
"""
Test the config cache issue
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_config_manager_cache():
    """Test if ConfigManager is caching old data"""
    print("🔍 Testing ConfigManager Cache")
    print("=" * 35)
    
    try:
        from config_manager import ConfigManager
        
        # Create a fresh ConfigManager instance
        config_manager = ConfigManager()
        print(f"✅ ConfigManager created")
        print(f"   Config path: {config_manager.config_path}")
        
        # Check what's in the config
        print(f"   Config sections: {list(config_manager.config.keys())}")
        
        if 'modules' in config_manager.config:
            print(f"   Modules in cache: {config_manager.config['modules']}")
        else:
            print(f"   No modules section in cache")
        
        # Force reload
        print(f"\n🔄 Forcing reload...")
        config_manager.reload()
        
        print(f"   Config sections after reload: {list(config_manager.config.keys())}")
        
        if 'modules' in config_manager.config:
            print(f"   Modules after reload: {config_manager.config['modules']}")
        else:
            print(f"   No modules section after reload")
        
        # Check the actual file
        print(f"\n📁 Checking actual config file...")
        if config_manager.config_path.exists():
            import json
            with open(config_manager.config_path, 'r') as f:
                file_config = json.load(f)
            
            print(f"   File sections: {list(file_config.keys())}")
            
            if 'modules' in file_config:
                print(f"   Modules in file: {file_config['modules']}")
            else:
                print(f"   No modules section in file")
        
        return True
        
    except Exception as e:
        print(f"❌ ConfigManager cache test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_old_config_file():
    """Check if there's an old config file causing issues"""
    print("\n🗂️  Checking for Old Config Files")
    print("=" * 35)
    
    try:
        # Check project directory
        project_config = Path(__file__).parent / "config.json"
        print(f"Project config: {project_config}")
        print(f"   Exists: {project_config.exists()}")
        
        if project_config.exists():
            print(f"   ❌ Old config file still exists!")
            with open(project_config, 'r') as f:
                import json
                old_config = json.load(f)
            print(f"   Old config sections: {list(old_config.keys())}")
            if 'modules' in old_config:
                print(f"   Old modules: {old_config['modules']}")
        
        # Check user directory
        user_config = Path.home() / "Library" / "Application Support" / "ClipboardMonitor" / "config.json"
        print(f"\nUser config: {user_config}")
        print(f"   Exists: {user_config.exists()}")
        
        if user_config.exists():
            with open(user_config, 'r') as f:
                import json
                user_config_data = json.load(f)
            print(f"   User config sections: {list(user_config_data.keys())}")
            if 'modules' in user_config_data:
                print(f"   User modules: {user_config_data['modules']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Old config file check failed: {e}")
        return False

def main():
    """Run cache tests"""
    print("🧪 Testing Config Cache Issues")
    print("=" * 40)
    
    cache_ok = test_config_manager_cache()
    old_file_ok = test_old_config_file()
    
    print("\n" + "=" * 40)
    print("📊 Cache Test Results:")
    print(f"   ConfigManager: {'✅ OK' if cache_ok else '❌ ISSUES'}")
    print(f"   Old Files: {'✅ OK' if old_file_ok else '❌ ISSUES'}")
    
    return cache_ok and old_file_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
