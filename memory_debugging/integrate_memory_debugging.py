#!/usr/bin/env python3
"""
Quick Integration Script for Memory Debugging

This script automatically integrates memory debugging into the menu bar app
by adding the necessary imports and decorators to suspect functions.

Usage:
    python3 integrate_memory_debugging.py [--apply] [--revert]
"""

import os
import sys
import re
import argparse
import shutil
from datetime import datetime

class MemoryDebuggingIntegrator:
    def __init__(self):
        self.menu_bar_file = "../menu_bar_app.py"
        self.backup_file = f"../menu_bar_app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        
        # Functions to profile (likely leak sources)
        self.functions_to_profile = [
            ('update_status', 'debug_timer_memory("status_update")'),
            ('update_memory_status', 'debug_timer_memory("memory_status")'),
            ('update_recent_history', 'monitor_history("recent_history_update")'),
            ('copy_history_item', 'debug_memory_usage("copy_history")'),
            ('_rebuild_menu', 'debug_memory_usage("rebuild_menu")'),
            ('update_status_periodically', 'debug_timer_memory("status_periodic")'),
            ('initial_history_update', 'debug_memory_usage("initial_history")')
        ]
        
        # Import statements to add
        self.import_statements = '''
# Memory debugging imports
try:
    from memory_debugging import (
        memory_profile,
        log_memory,
        activate_memory_debugging,
        debug_timer_memory,
        monitor_history,
        add_checkpoint,
        debug_memory_usage,
        check_increase
    )
    MEMORY_DEBUG_AVAILABLE = True
    print("Memory debugging enabled")
except ImportError as e:
    MEMORY_DEBUG_AVAILABLE = False
    print(f"Memory debugging not available: {e}")
'''
        
        # Initialization code to add
        self.init_code = '''
        # Activate memory debugging
        if MEMORY_DEBUG_AVAILABLE:
            activate_memory_debugging()
            log_memory("Menu bar app initialized with memory debugging")
'''
    
    def backup_original_file(self):
        """Create a backup of the original file."""
        if not os.path.exists(self.menu_bar_file):
            print(f"Error: {self.menu_bar_file} not found!")
            return False
        
        try:
            shutil.copy2(self.menu_bar_file, self.backup_file)
            print(f"Backup created: {self.backup_file}")
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def add_imports(self, content):
        """Add memory debugging imports to the file."""
        # Find the position after the last import
        import_pattern = r'^(import\s+\w+|from\s+\w+.*import.*)'
        lines = content.split('\n')
        
        last_import_line = -1
        for i, line in enumerate(lines):
            if re.match(import_pattern, line.strip()):
                last_import_line = i
        
        if last_import_line == -1:
            # No imports found, add at the beginning
            last_import_line = 0
        
        # Insert the memory debugging imports
        lines.insert(last_import_line + 1, self.import_statements)
        
        return '\n'.join(lines)
    
    def add_initialization(self, content):
        """Add memory debugging initialization to the __init__ method."""
        # Find the ClipboardMonitorMenuBar class __init__ method
        lines = content.split('\n')

        # Look for the specific pattern in the ClipboardMonitorMenuBar __init__
        for i, line in enumerate(lines):
            if 'def __init__(self):' in line and i > 0:
                # Check if this is inside the ClipboardMonitorMenuBar class
                for j in range(i-1, max(0, i-20), -1):
                    if 'class ClipboardMonitorMenuBar' in lines[j]:
                        # Found the right __init__ method
                        # Look for the end of the initialization (before self.run())
                        for k in range(i+1, min(len(lines), i+50)):
                            if 'self.run()' in lines[k]:
                                # Insert initialization code before self.run()
                                lines.insert(k, self.init_code)
                                return '\n'.join(lines)
                        break

        return content
    
    def add_function_decorators(self, content):
        """Add memory debugging decorators to suspect functions."""
        lines = content.split('\n')
        
        for func_name, decorator in self.functions_to_profile:
            # Find the function definition
            func_pattern = rf'^\s*def {func_name}\(self.*?\):'
            
            for i, line in enumerate(lines):
                if re.match(func_pattern, line):
                    # Check if decorator already exists
                    if i > 0 and decorator.split('(')[0] in lines[i-1]:
                        continue  # Already decorated
                    
                    # Add the decorator
                    indent = len(line) - len(line.lstrip())
                    decorator_line = ' ' * indent + f'@{decorator}'
                    lines.insert(i, decorator_line)
                    print(f"Added decorator to {func_name}")
                    break
        
        return '\n'.join(lines)
    
    def add_memory_checkpoints(self, content):
        """Add memory checkpoints to critical operations."""
        # Add checkpoints to specific functions
        checkpoint_additions = [
            {
                'function': 'copy_history_item',
                'start_checkpoint': '''        if MEMORY_DEBUG_AVAILABLE:
            add_checkpoint("before_copy_history", "copy_history_item")''',
                'end_checkpoint': '''        if MEMORY_DEBUG_AVAILABLE:
            check_increase("before_copy_history", threshold_mb=1.0)'''
            },
            {
                'function': '_rebuild_menu',
                'start_checkpoint': '''        if MEMORY_DEBUG_AVAILABLE:
            add_checkpoint("before_menu_rebuild", "_rebuild_menu")''',
                'end_checkpoint': '''        if MEMORY_DEBUG_AVAILABLE:
            check_increase("before_menu_rebuild", threshold_mb=2.0)'''
            }
        ]
        
        lines = content.split('\n')
        
        for checkpoint in checkpoint_additions:
            func_name = checkpoint['function']
            func_pattern = rf'^\s*def {func_name}\(self.*?\):'
            
            for i, line in enumerate(lines):
                if re.match(func_pattern, line):
                    # Add start checkpoint after function definition
                    lines.insert(i + 1, checkpoint['start_checkpoint'])
                    
                    # Find the end of the function and add end checkpoint
                    # This is simplified - in practice, you'd want more sophisticated parsing
                    for j in range(i + 2, len(lines)):
                        if lines[j].strip().startswith('def ') or (j == len(lines) - 1):
                            lines.insert(j, checkpoint['end_checkpoint'])
                            break
                    
                    print(f"Added memory checkpoints to {func_name}")
                    break
        
        return '\n'.join(lines)
    
    def apply_memory_debugging(self):
        """Apply memory debugging integration to the menu bar app."""
        print("Applying memory debugging integration...")
        
        # Create backup
        if not self.backup_original_file():
            return False
        
        try:
            # Read the original file
            with open(self.menu_bar_file, 'r') as f:
                content = f.read()
            
            # Apply modifications
            print("Adding imports...")
            content = self.add_imports(content)
            
            print("Adding initialization...")
            content = self.add_initialization(content)
            
            print("Adding function decorators...")
            content = self.add_function_decorators(content)
            
            print("Adding memory checkpoints...")
            content = self.add_memory_checkpoints(content)
            
            # Write the modified file
            with open(self.menu_bar_file, 'w') as f:
                f.write(content)
            
            print(f"✅ Memory debugging integration applied successfully!")
            print(f"📁 Backup saved as: {self.backup_file}")
            print("\n🚀 Next steps:")
            print("1. Restart the menu bar app: ./restart_menubar.sh")
            print("2. Monitor memory usage: tail -f memory_leak_debug.log")
            print("3. Run live analysis: python3 memory_leak_analyzer.py --live")
            
            return True
            
        except Exception as e:
            print(f"Error applying memory debugging: {e}")
            return False

    def revert_changes(self):
        """Revert to the most recent backup."""
        # Find the most recent backup
        backup_files = [f for f in os.listdir('..') if f.startswith('menu_bar_app_backup_')]
        
        if not backup_files:
            print("No backup files found!")
            return False
        
        # Sort by timestamp (newest first)
        backup_files.sort(reverse=True)
        latest_backup = backup_files[0]
        
        try:
            shutil.copy2(latest_backup, self.menu_bar_file)
            print(f"✅ Reverted to backup: {latest_backup}")
            return True
        except Exception as e:
            print(f"Error reverting changes: {e}")
            return False
    
    def show_status(self):
        """Show current status of memory debugging integration."""
        if not os.path.exists(self.menu_bar_file):
            print(f"❌ {self.menu_bar_file} not found!")
            return
        
        try:
            with open(self.menu_bar_file, 'r') as f:
                content = f.read()
            
            # Check for memory debugging imports
            has_imports = 'memory_leak_debugger' in content
            has_activation = 'activate_memory_debugging' in content
            
            # Count decorated functions
            decorated_functions = 0
            for func_name, decorator in self.functions_to_profile:
                if decorator.split('(')[0] in content:
                    decorated_functions += 1
            
            print("📊 Memory Debugging Integration Status:")
            print(f"   Imports added: {'✅' if has_imports else '❌'}")
            print(f"   Activation code: {'✅' if has_activation else '❌'}")
            print(f"   Decorated functions: {decorated_functions}/{len(self.functions_to_profile)}")
            
            # Check for backup files
            backup_files = [f for f in os.listdir('..') if f.startswith('menu_bar_app_backup_')]
            print(f"   Available backups: {len(backup_files)}")
            
        except Exception as e:
            print(f"Error checking status: {e}")

def main():
    parser = argparse.ArgumentParser(description='Memory Debugging Integration Tool')
    parser.add_argument('--apply', action='store_true', help='Apply memory debugging integration')
    parser.add_argument('--revert', action='store_true', help='Revert to backup')
    parser.add_argument('--status', action='store_true', help='Show integration status')
    
    args = parser.parse_args()
    
    integrator = MemoryDebuggingIntegrator()
    
    if args.apply:
        integrator.apply_memory_debugging()
    elif args.revert:
        integrator.revert_changes()
    elif args.status:
        integrator.show_status()
    else:
        print("Memory Debugging Integration Tool")
        print("Usage:")
        print("  --apply   Apply memory debugging integration")
        print("  --revert  Revert to backup")
        print("  --status  Show current status")

if __name__ == "__main__":
    main()
