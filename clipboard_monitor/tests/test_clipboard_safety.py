#!/usr/bin/env python3
"""
Test script to verify that clipboard content is not modified inappropriately.
This script tests various content types to ensure only intended modifications occur.
"""

import sys
import os
import pyperclip
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules import markdown_module, mermaid_module, code_formatter_module, history_module

def test_content_safety():
    """Test that modules don't modify clipboard content inappropriately"""

    # Check configuration first
    print("🔧 Checking module configuration...")
    try:
        import json
        with open('config.json', 'r') as f:
            config = json.load(f)
        markdown_modify = config.get('modules', {}).get('markdown_modify_clipboard', True)
        print(f"  Markdown modify clipboard: {markdown_modify}")
    except Exception as e:
        print(f"  ⚠️  Could not read config: {e}")

    test_cases = [
        {
            "name": "Plain Text",
            "content": "This is just plain text that should never be modified.",
            "should_modify": False
        },
        {
            "name": "Email Content",
            "content": "Hi John,\n\nHope you're doing well. Let's meet tomorrow at 3pm.\n\nBest,\nAlice",
            "should_modify": False
        },
        {
            "name": "URL",
            "content": "https://www.example.com/some/path?param=value",
            "should_modify": False
        },
        {
            "name": "JSON Data",
            "content": '{"name": "John", "age": 30, "city": "New York"}',
            "should_modify": False
        },
        {
            "name": "Code (with modification disabled)",
            "content": "def hello():\n    print('Hello, World!')\n    return True",
            "should_modify": False  # Code formatter is disabled by default
        },
        {
            "name": "Markdown (with modification enabled)",
            "content": "# Test Heading\n\nThis is **bold** text and *italic* text.\n\n* List item 1\n* List item 2",
            "should_modify": True  # Markdown module should convert this
        },
        {
            "name": "Mermaid Diagram",
            "content": "graph TD\n    A[Start] --> B{Decision}\n    B --> C[End]",
            "should_modify": False  # Mermaid module only opens browser, doesn't modify clipboard
        },
        {
            "name": "Mixed Content",
            "content": "Here's some text with (parentheses) and other content that shouldn't be touched.",
            "should_modify": False
        }
    ]
    
    print("🧪 Testing Clipboard Safety")
    print("=" * 50)
    
    results = []
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"Content: {test_case['content'][:50]}{'...' if len(test_case['content']) > 50 else ''}")
        
        # Set clipboard content
        original_content = test_case['content']
        pyperclip.copy(original_content)
        
        # Wait a moment
        time.sleep(0.1)
        
        # Test each module
        modules_to_test = [
            ("Markdown", markdown_module),
            ("Mermaid", mermaid_module),
            ("Code Formatter", code_formatter_module),
            ("History", history_module)
        ]
        
        clipboard_modified = False
        
        for module_name, module in modules_to_test:
            try:
                # Store original clipboard content before processing
                pyperclip.copy(original_content)
                time.sleep(0.1)  # Small delay to ensure clipboard is set

                # Process with module
                result = module.process(original_content)

                # Check if clipboard was modified
                current_clipboard = pyperclip.paste()
                if current_clipboard != original_content:
                    clipboard_modified = True
                    print(f"  ⚠️  {module_name} module modified clipboard!")
                    print(f"    Original: {original_content[:30]}...")
                    print(f"    Modified: {current_clipboard[:30]}...")

                    # Reset clipboard for next test
                    pyperclip.copy(original_content)
                    time.sleep(0.1)
                else:
                    print(f"  ✅ {module_name} module did not modify clipboard")

            except Exception as e:
                print(f"  ❌ {module_name} module error: {e}")
                # Reset clipboard in case of error
                pyperclip.copy(original_content)
                time.sleep(0.1)
        
        # Check if modification behavior matches expectation
        if clipboard_modified == test_case['should_modify']:
            print(f"  🎯 PASS: Modification behavior as expected")
            results.append(("PASS", test_case['name']))
        else:
            expected = "should modify" if test_case['should_modify'] else "should NOT modify"
            actual = "was modified" if clipboard_modified else "was NOT modified"
            print(f"  ❌ FAIL: Expected {expected}, but clipboard {actual}")
            results.append(("FAIL", test_case['name']))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for result, _ in results if result == "PASS")
    total = len(results)
    
    for result, name in results:
        status_icon = "✅" if result == "PASS" else "❌"
        print(f"{status_icon} {result}: {name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Clipboard safety is maintained.")
        return True
    else:
        print("⚠️  Some tests failed. Please review module behavior.")
        return False

if __name__ == "__main__":
    success = test_content_safety()
    sys.exit(0 if success else 1)
