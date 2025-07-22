#!/usr/bin/env python3
"""
Simple Memory Debugging Application Script
"""

import os
import shutil
from datetime import datetime

def apply_memory_debugging():
    """Apply memory debugging to menu_bar_app.py"""
    
    print("🔍 Applying Memory Debugging Integration...")
    
    # Create backup
    backup_name = f"../menu_bar_app_backup_simple_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    try:
        shutil.copy2("../menu_bar_app.py", backup_name)
        print(f"✅ Backup created: {backup_name}")
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False
    
    try:
        # Read the file
        with open("../menu_bar_app.py", "r") as f:
            content = f.read()
        
        # Simple approach: Add imports after the existing imports
        import_code = '''
# Memory debugging imports
try:
    from memory_debugging import activate_memory_debugging, debug_timer_memory, log_memory
    MEMORY_DEBUG_AVAILABLE = True
    print("✅ Memory debugging enabled")
except ImportError as e:
    MEMORY_DEBUG_AVAILABLE = False
    print(f"⚠️  Memory debugging not available: {e}")
'''
        
        # Find the last import and add our imports after it
        lines = content.split('\n')
        last_import_line = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith(('import ', 'from ')) and not line.strip().startswith('#'):
                last_import_line = i
        
        if last_import_line != -1:
            lines.insert(last_import_line + 1, import_code)
        
        # Add initialization in __init__ method
        init_code = '''
        # Activate memory debugging
        if MEMORY_DEBUG_AVAILABLE:
            activate_memory_debugging()
            log_memory("Menu bar app initialized with memory debugging")
'''
        
        # Find self.run() and add initialization before it
        for i, line in enumerate(lines):
            if 'self.run()' in line.strip():
                lines.insert(i, init_code)
                break
        
        # Add decorators to key functions
        decorators_added = 0
        
        # Look for update_status method
        for i, line in enumerate(lines):
            if 'def update_status(self):' in line:
                indent = len(line) - len(line.lstrip())
                decorator = ' ' * indent + '@debug_timer_memory("status_update")'
                lines.insert(i, decorator)
                decorators_added += 1
                print("✅ Added decorator to update_status")
                break
        
        # Look for update_memory_status method
        for i, line in enumerate(lines):
            if 'def update_memory_status(self, _):' in line:
                indent = len(line) - len(line.lstrip())
                decorator = ' ' * indent + '@debug_timer_memory("memory_status")'
                lines.insert(i, decorator)
                decorators_added += 1
                print("✅ Added decorator to update_memory_status")
                break
        
        # Write the modified content
        with open("../menu_bar_app.py", "w") as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Memory debugging integration completed!")
        print(f"📊 Added {decorators_added} function decorators")
        print(f"📁 Backup: {backup_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration failed: {e}")
        # Restore backup
        try:
            shutil.copy2(backup_name, "../menu_bar_app.py")
            print("✅ Restored from backup")
        except:
            print("❌ Failed to restore backup")
        return False

if __name__ == "__main__":
    if apply_memory_debugging():
        print("\n🚀 Next Steps:")
        print("1. cd .. && ./restart_menubar.sh")
        print("2. tail -f memory_leak_debug.log")
        print("3. python3 memory_debugging/memory_leak_analyzer.py --live")
    else:
        print("\n❌ Integration failed. Please check the errors above.")
