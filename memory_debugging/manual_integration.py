#!/usr/bin/env python3
"""
Manual Memory Debugging Integration

This script provides a more targeted approach to integrating memory debugging
by making specific, precise changes to the menu bar app.
"""

import os
import shutil
from datetime import datetime

def backup_file():
    """Create a backup of the menu bar app."""
    source = "../menu_bar_app.py"
    backup = f"../menu_bar_app_backup_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    try:
        shutil.copy2(source, backup)
        print(f"✅ Backup created: {backup}")
        return backup
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return None

def add_memory_debugging():
    """Add memory debugging with precise modifications."""
    
    # Step 1: Create backup
    backup_file_path = backup_file()
    if not backup_file_path:
        return False
    
    try:
        # Step 2: Read the file
        with open("../menu_bar_app.py", "r") as f:
            content = f.read()
        
        # Step 3: Add imports at the top (after existing imports)
        import_addition = '''
# Memory debugging imports
try:
    from memory_debugging import (
        activate_memory_debugging, 
        debug_timer_memory,
        log_memory
    )
    MEMORY_DEBUG_AVAILABLE = True
    print("✅ Memory debugging enabled")
except ImportError as e:
    MEMORY_DEBUG_AVAILABLE = False
    print(f"⚠️  Memory debugging not available: {e}")
'''
        
        # Find a good place to insert imports (after the last import)
        lines = content.split('\n')
        insert_line = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                insert_line = i + 1
        
        lines.insert(insert_line, import_addition)
        
        # Step 4: Add initialization in the __init__ method
        init_addition = '''
        # Activate memory debugging
        if MEMORY_DEBUG_AVAILABLE:
            activate_memory_debugging()
            log_memory("Menu bar app initialized with memory debugging")
'''
        
        # Find the ClipboardMonitorMenuBar __init__ method and add before self.run()
        for i, line in enumerate(lines):
            if 'self.run()' in line and 'ClipboardMonitorMenuBar' in ''.join(lines[max(0, i-50):i]):
                lines.insert(i, init_addition)
                break
        
        # Step 5: Add decorators to key functions
        functions_to_decorate = [
            ('def update_status(self)', '@debug_timer_memory("status_update")'),
            ('def update_memory_status(self, _)', '@debug_timer_memory("memory_status")'),
        ]
        
        for i, line in enumerate(lines):
            for func_signature, decorator in functions_to_decorate:
                if func_signature in line:
                    # Get the indentation of the function
                    indent = len(line) - len(line.lstrip())
                    decorator_line = ' ' * indent + decorator
                    lines.insert(i, decorator_line)
                    print(f"✅ Added decorator to {func_signature}")
                    break
        
        # Step 6: Write the modified content
        modified_content = '\n'.join(lines)
        
        with open("../menu_bar_app.py", "w") as f:
            f.write(modified_content)
        
        print("✅ Memory debugging integration completed successfully!")
        print(f"📁 Backup saved as: {backup_file_path}")
        print("\n🚀 Next steps:")
        print("1. cd .. && ./restart_menubar.sh")
        print("2. tail -f memory_leak_debug.log")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during integration: {e}")
        # Restore backup
        try:
            shutil.copy2(backup_file_path, "../menu_bar_app.py")
            print("✅ Restored from backup")
        except:
            print("❌ Failed to restore backup")
        return False

def start_live_monitoring():
    """Start live memory monitoring."""
    print("🔍 Starting live memory monitoring...")
    print("This will monitor the menu bar app for 1 hour and generate a report.")
    print("Press Ctrl+C to stop early.\n")
    
    import subprocess
    try:
        subprocess.run([
            "python3", "memory_leak_analyzer.py", 
            "--live", "--duration=3600", "--interval=30", "--graph"
        ])
    except KeyboardInterrupt:
        print("\n✅ Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")

def main():
    print("🔍 Manual Memory Debugging Integration")
    print("=" * 50)
    
    choice = input("""
Choose an option:
1. Apply memory debugging integration
2. Start live monitoring (without integration)
3. Both (integrate then monitor)

Enter choice (1-3): """).strip()
    
    if choice == "1":
        add_memory_debugging()
    elif choice == "2":
        start_live_monitoring()
    elif choice == "3":
        if add_memory_debugging():
            print("\n" + "="*50)
            print("Integration complete! Now starting monitoring...")
            print("Please restart the menu bar app first:")
            print("cd .. && ./restart_menubar.sh")
            input("Press Enter after restarting the app to begin monitoring...")
            start_live_monitoring()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
