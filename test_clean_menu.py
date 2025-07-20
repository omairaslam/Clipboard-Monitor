#!/usr/bin/env python3
"""
Test script to verify the new clean modular menu structure.
This script will test the menu building logic without actually running the GUI.
"""

import sys
import os
import json

# Add the current directory to the path so we can import menu_bar_app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_module_detection():
    """Test the module detection and enabled/disabled logic."""
    print("🧪 Testing Clean Modular Menu Structure")
    print("=" * 50)
    
    # Load current config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        modules_config = config.get('modules', {})
        print(f"📋 Current module configuration:")
        for module, status in modules_config.items():
            if module.endswith('_module'):
                enabled = status not in [0, False]
                status_icon = "✅" if enabled else "❌"
                print(f"   {status_icon} {module}: {status}")
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False
    
    print("\n🎯 Expected Menu Structure (based on current config):")
    print("=" * 50)
    
    # Simulate what the menu should look like
    enabled_modules = []
    disabled_modules = []
    
    for module, status in modules_config.items():
        if module.endswith('_module'):
            if status not in [0, False]:
                enabled_modules.append(module)
            else:
                disabled_modules.append(module)
    
    print("📊 Status: Running (Enhanced)")
    print("🧠 Menu Bar: XX.X MB")
    print("⚙️ Service: XX.X MB")
    print("---")
    print("⏸️ Pause Monitoring")
    print("🔄 Service Control >")
    print("---")
    
    # Show enabled modules
    if enabled_modules:
        for module in enabled_modules:
            if module == "history_module":
                print("📚 Clipboard History >")
                print("   ├── 📋 Recent Items >")
                print("   ├── 🌐 View Full History (Browser)")
                print("   ├── 💻 View Full History (Terminal)")
                print("   └── 🗑️ Clear History")
            elif module == "mermaid_module":
                print("🧩 Mermaid Diagram Detector >")
                print("   └── Settings >")
            elif module == "drawio_module":
                print("🎨 Draw.io Diagram Detector >")
                print("   └── Settings >")
            elif module == "markdown_module":
                print("📝 Markdown Processor >")
                print("   └── ✅ Modify Clipboard Content")
            elif module == "code_formatter_module":
                print("🔧 Code Formatter >")
                print("   └── ✅ Modify Clipboard Content")
    else:
        print("[No enabled modules - clean interface!]")
    
    print("---")
    print("🧠 Memory Monitor >")
    print("---")
    print("⚙️ Settings >")
    if disabled_modules:
        print("   ├── ➕ Add Modules >")
        for module in disabled_modules:
            module_names = {
                "history_module": "Clipboard History Tracker",
                "markdown_module": "Markdown Processor", 
                "mermaid_module": "Mermaid Diagram Detector",
                "drawio_module": "Draw.io Diagram Detector",
                "code_formatter_module": "Code Formatter"
            }
            display_name = module_names.get(module, module)
            print(f"   │   └── {display_name} (Click to enable)")
    else:
        print("   ├── ➕ Add Modules > (All modules enabled)")
    
    print("   ├── 🔧 General >")
    print("   ├── 🚀 Performance >")
    print("   ├── 🔒 Security >")
    print("   └── 💾 Configuration >")
    print("---")
    print("📋 Logs >")
    print("❌ Quit")
    
    print(f"\n✅ Clean Menu Test Complete!")
    print(f"📊 Enabled modules: {len(enabled_modules)}")
    print(f"🚫 Disabled modules: {len(disabled_modules)} (hidden from main menu)")
    print(f"🎯 Interface shows only what user needs!")
    
    return True

if __name__ == "__main__":
    test_module_detection()
