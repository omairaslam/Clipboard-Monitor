#!/usr/bin/env python3
"""
Test script for the full clipboard menu integration with popup functionality.
"""

import sys
import os
import json
import time
from pathlib import Path

sys.path.append(os.path.dirname(__file__))

from utils import safe_expanduser, ensure_directory_exists

def create_test_clipboard_history():
    """Create test clipboard history data."""
    history_path = safe_expanduser("~/Library/Application Support/ClipboardMonitor/clipboard_history.json")
    ensure_directory_exists(os.path.dirname(history_path))
    
    # Create test data with various content types
    test_history = [
        {
            "content": "This is a short clipboard entry",
            "timestamp": time.time() - 60,  # 1 minute ago
            "hash": "hash1"
        },
        {
            "content": """This is a much longer clipboard entry that contains multiple lines.
It has various types of content including:
- Bullet points
- Code snippets: print("Hello, World!")
- Special characters: !@#$%^&*()
- Unicode emojis: 🎉 📋 ✨ 🚀

This entry is designed to test the popup window's ability to display
longer content with proper formatting and scrolling capabilities.

The popup should show this complete content when you hold the Option key
and click on the menu item, while a normal click should copy the content
to the clipboard as usual.""",
            "timestamp": time.time() - 120,  # 2 minutes ago
            "hash": "hash2"
        },
        {
            "content": "https://github.com/example/repository",
            "timestamp": time.time() - 180,  # 3 minutes ago
            "hash": "hash3"
        },
        {
            "content": """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate first 10 Fibonacci numbers
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")""",
            "timestamp": time.time() - 240,  # 4 minutes ago
            "hash": "hash4"
        },
        {
            "content": "Simple text with special chars: àáâãäåæçèéêë",
            "timestamp": time.time() - 300,  # 5 minutes ago
            "hash": "hash5"
        }
    ]
    
    # Save test history
    with open(history_path, 'w') as f:
        json.dump(test_history, f, indent=2)
    
    print(f"✅ Created test clipboard history at: {history_path}")
    print(f"📊 Created {len(test_history)} test entries")
    
    return history_path

def test_menu_integration():
    """Test the menu integration with popup functionality."""
    try:
        # Create test data
        history_path = create_test_clipboard_history()
        
        print("\n🧪 Testing menu integration...")
        print("📋 Test clipboard history created")
        print("🎯 You can now test the functionality by:")
        print("   1. Running the menu bar app: python3 menu_bar_app.py")
        print("   2. Clicking on the clipboard icon in the menu bar")
        print("   3. Going to 'Recent Clipboard Items'")
        print("   4. Normal click = Copy to clipboard")
        print("   5. Option + Click = Show full content preview popup")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing clipboard menu integration with popup functionality...")
    success = test_menu_integration()
    if success:
        print("\n✅ Integration test setup completed!")
        print("🚀 Ready to test the popup functionality!")
    else:
        print("\n❌ Integration test failed!")
