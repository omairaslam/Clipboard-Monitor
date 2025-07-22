#!/usr/bin/env python3
"""
Minimal test script to isolate menu callback issues.
This will help determine if the problem is with rumps, our callback setup, or something else.
"""

import rumps
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestMenuApp(rumps.App):
    def __init__(self):
        super(TestMenuApp, self).__init__("🧪 Test", quit_button=None)
        print("DEBUG: TestMenuApp initialized")
        self.create_test_menu()
        
    def create_test_menu(self):
        """Create a simple test menu to verify callbacks work."""
        print("DEBUG: Creating test menu...")
        
        # Test 1: Simple callback
        test1 = rumps.MenuItem("Test 1: Simple Callback", callback=self.test_callback_1)
        self.menu.add(test1)
        print(f"DEBUG: Added Test 1, callback: {test1.callback}")
        
        # Test 2: Theme-like submenu
        theme_menu = rumps.MenuItem("Test 2: Theme Menu")
        
        themes = ["Light", "Dark", "Forest", "Neutral"]
        for theme in themes:
            item = rumps.MenuItem(theme, callback=self.test_theme_callback)
            theme_menu.add(item)
            print(f"DEBUG: Added theme '{theme}', callback: {item.callback}")
        
        self.menu.add(theme_menu)
        
        # Test 3: Quit button
        quit_item = rumps.MenuItem("Quit Test", callback=self.quit_test)
        self.menu.add(quit_item)
        
        print("DEBUG: Test menu creation complete")
    
    def test_callback_1(self, sender):
        """Simple test callback."""
        print(f"SUCCESS: test_callback_1 triggered! Sender: {sender.title}")
        rumps.notification("Test Success", "Callback 1 Worked", f"Clicked: {sender.title}")
    
    def test_theme_callback(self, sender):
        """Test theme-like callback."""
        print(f"SUCCESS: test_theme_callback triggered! Theme: {sender.title}")

        # Update menu states like the real theme menu
        # Try different approaches to iterate over sibling menu items
        try:
            # Approach 1: Try itervalues()
            print("DEBUG: Trying sender.parent.itervalues()...")
            for item in sender.parent.itervalues():
                if isinstance(item, rumps.MenuItem):
                    old_state = item.state
                    item.state = (item.title == sender.title)
                    print(f"DEBUG: '{item.title}' state: {old_state} -> {item.state}")
        except AttributeError as e:
            print(f"DEBUG: itervalues() failed: {e}")

            # Approach 2: Try direct iteration
            try:
                print("DEBUG: Trying direct iteration over sender.parent...")
                for item in sender.parent:
                    if isinstance(item, rumps.MenuItem):
                        old_state = item.state
                        item.state = (item.title == sender.title)
                        print(f"DEBUG: '{item.title}' state: {old_state} -> {item.state}")
            except Exception as e2:
                print(f"DEBUG: Direct iteration failed: {e2}")

                # Approach 3: Try accessing parent's values
                try:
                    print("DEBUG: Trying sender.parent.values()...")
                    for item in sender.parent.values():
                        if isinstance(item, rumps.MenuItem):
                            old_state = item.state
                            item.state = (item.title == sender.title)
                            print(f"DEBUG: '{item.title}' state: {old_state} -> {item.state}")
                except Exception as e3:
                    print(f"DEBUG: values() failed: {e3}")
                    print("DEBUG: Unable to iterate over menu items")

        rumps.notification("Theme Test", "Theme Callback Worked", f"Selected: {sender.title}")
    
    def quit_test(self, sender):
        """Quit the test app."""
        print("DEBUG: Quitting test app...")
        rumps.quit_application()

if __name__ == "__main__":
    print("=== MENU CALLBACK TEST STARTING ===")
    print("This test will help isolate the callback issue.")
    print("Try clicking the menu items to see if callbacks work.")
    print("=====================================")
    
    app = TestMenuApp()
    app.run()
