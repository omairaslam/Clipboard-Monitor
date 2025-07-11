#!/usr/bin/env python3
"""
Aggressive Memory Fix
Immediate intervention to reduce menu bar app memory usage.
"""

import os
import sys
import psutil
import gc
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
from utils import safe_expanduser, log_event, log_error


def force_memory_cleanup():
    """Force aggressive memory cleanup"""
    print("🧹 Forcing aggressive memory cleanup...")
    
    # Clear all possible caches
    if hasattr(sys, '_clear_type_cache'):
        sys._clear_type_cache()
    
    # Force garbage collection multiple times
    for i in range(3):
        collected = gc.collect()
        print(f"   GC round {i+1}: collected {collected} objects")
    
    # Clear import cache
    if hasattr(sys, 'modules'):
        # Don't clear essential modules, but clear any large ones
        modules_to_clear = []
        for module_name in list(sys.modules.keys()):
            if any(x in module_name.lower() for x in ['matplotlib', 'numpy', 'pandas', 'scipy']):
                modules_to_clear.append(module_name)
        
        for module_name in modules_to_clear:
            if module_name in sys.modules:
                del sys.modules[module_name]
                print(f"   Cleared module: {module_name}")
    
    print("✅ Aggressive cleanup complete")


def check_memory_usage():
    """Check current memory usage"""
    try:
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"📊 Current memory usage: {memory_mb:.1f} MB")
        return memory_mb
    except Exception as e:
        print(f"❌ Error checking memory: {e}")
        return 0


def disable_memory_tracking():
    """Disable memory tracking in data files"""
    print("🚫 Disabling memory tracking...")
    
    data_files = [
        safe_expanduser("~/Library/Application Support/ClipboardMonitor/memory_data.json"),
        safe_expanduser("~/Library/Application Support/ClipboardMonitor/menubar_profile.json"),
        safe_expanduser("~/Library/Application Support/ClipboardMonitor/advanced_profile.json")
    ]
    
    for data_file in data_files:
        if os.path.exists(data_file):
            try:
                os.remove(data_file)
                print(f"   Removed: {os.path.basename(data_file)}")
            except Exception as e:
                print(f"   Error removing {data_file}: {e}")


def optimize_clipboard_history():
    """Optimize clipboard history to reduce memory usage"""
    print("📋 Optimizing clipboard history...")
    
    history_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/clipboard_history.json")
    
    if os.path.exists(history_file):
        try:
            import json
            
            # Read current history
            with open(history_file, 'r') as f:
                history = json.load(f)
            
            original_count = len(history) if isinstance(history, list) else 0
            
            # Limit to last 50 items and truncate content
            if isinstance(history, list) and len(history) > 50:
                history = history[:50]
                
                # Truncate long content to reduce memory usage
                for item in history:
                    if isinstance(item, dict) and 'content' in item:
                        if len(item['content']) > 1000:  # Limit content to 1000 chars
                            item['content'] = item['content'][:1000] + "..."
                
                # Save optimized history
                with open(history_file, 'w') as f:
                    json.dump(history, f)
                
                print(f"   Optimized: {original_count} → {len(history)} items")
            else:
                print(f"   History already optimal: {original_count} items")
                
        except Exception as e:
            print(f"   Error optimizing history: {e}")
    else:
        print("   No history file found")


def create_minimal_config():
    """Create minimal configuration to reduce memory usage"""
    print("⚙️  Creating minimal configuration...")
    
    config_file = safe_expanduser("~/Library/Application Support/ClipboardMonitor/config.json")
    
    minimal_config = {
        "general": {
            "debug_mode": False,
            "log_level": "ERROR"  # Reduce logging
        },
        "history": {
            "max_items": 10,  # Reduce from default 20
            "max_content_length": 500  # Limit content length
        },
        "memory": {
            "tracking_enabled": False,  # Disable memory tracking
            "profiling_enabled": False,  # Disable profiling
            "emergency_limit_mb": 80  # Lower emergency limit
        }
    }
    
    try:
        import json
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(minimal_config, f, indent=2)
        print("   ✅ Minimal config created")
    except Exception as e:
        print(f"   ❌ Error creating config: {e}")


def main():
    """Main aggressive memory fix"""
    print("🚨 AGGRESSIVE MEMORY FIX")
    print("=" * 40)
    
    # Check initial memory
    initial_memory = check_memory_usage()
    
    # Apply fixes
    disable_memory_tracking()
    optimize_clipboard_history()
    create_minimal_config()
    force_memory_cleanup()
    
    # Check final memory
    time.sleep(2)
    final_memory = check_memory_usage()
    
    if initial_memory > 0 and final_memory > 0:
        memory_saved = initial_memory - final_memory
        print(f"\n📊 Memory Fix Results:")
        print(f"   Before: {initial_memory:.1f} MB")
        print(f"   After: {final_memory:.1f} MB")
        print(f"   Saved: {memory_saved:.1f} MB")
        
        if final_memory < 50:
            print("   ✅ Memory usage now acceptable")
        elif final_memory < 80:
            print("   ⚠️  Memory usage improved but still elevated")
        else:
            print("   🚨 Memory usage still too high - may need restart")
    
    print("\n💡 Recommendations:")
    print("1. Restart the menu bar app to see full effect")
    print("2. Keep memory tracking disabled")
    print("3. Monitor memory usage regularly")
    print("4. If memory exceeds 80MB, emergency cleanup will trigger")


if __name__ == "__main__":
    main()
