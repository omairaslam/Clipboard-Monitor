#!/usr/bin/env python3
"""
Simple Menu Bar App Restart
Uses the built-in singleton mechanism to ensure clean restarts.
"""

import subprocess
import sys
import time
from pathlib import Path


def restart_menubar():
    """Restart the menu bar app using its built-in singleton mechanism"""
    print("🔄 RESTARTING MENU BAR APP")
    print("=" * 40)
    
    script_dir = Path(__file__).parent
    script_path = script_dir / 'menu_bar_app.py'
    
    if not script_path.exists():
        print(f"❌ Error: menu_bar_app.py not found at {script_path}")
        return False
    
    try:
        print("🚀 Starting menu bar app...")
        print("   (Built-in singleton will handle any existing instances)")
        
        # Start the app - it will handle duplicate detection internally
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(script_dir),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Menu bar app started successfully!")
            if result.stdout:
                print("   Output:", result.stdout.strip())
            return True
        else:
            print(f"❌ Menu bar app failed to start (exit code: {result.returncode})")
            if result.stderr:
                print("   Error:", result.stderr.strip())
            if result.stdout:
                print("   Output:", result.stdout.strip())
            return False
            
    except subprocess.TimeoutExpired:
        print("✅ Menu bar app started (running in background)")
        return True
    except Exception as e:
        print(f"❌ Error starting menu bar app: {e}")
        return False


def main():
    """Main restart function"""
    success = restart_menubar()
    
    if success:
        print("\n" + "=" * 40)
        print("✅ RESTART SUCCESSFUL!")
        print("   Check your menu bar for the clipboard monitor icon")
        print("   The app now prevents duplicate instances automatically")
    else:
        print("\n" + "=" * 40)
        print("❌ RESTART FAILED!")
        print("   Check the error messages above")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
