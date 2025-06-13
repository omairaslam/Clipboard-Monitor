#!/bin/bash

# Clipboard Monitor - Dependency Installation Script
# This script installs the required Python dependencies for the clipboard monitor

echo "🔧 Installing Clipboard Monitor dependencies..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Install dependencies
echo "📦 Installing Python dependencies..."
python3 -m pip install --user -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
    echo ""
    echo "🧪 Testing pyobjc import..."
    python3 -c "
try:
    from AppKit import NSPasteboard, NSApplication, NSObject
    from Foundation import NSNotificationCenter, NSTimer, NSRunLoop, NSDefaultRunLoopMode
    import objc
    print('✅ pyobjc imports successful - enhanced monitoring available!')
except ImportError as e:
    print(f'❌ pyobjc import failed: {e}')
    print('💡 Try: python3 -m pip install --user pyobjc-framework-Cocoa')
"
    echo ""
    echo "🚀 You can now run the clipboard monitor with:"
    echo "   python3 main.py"
else
    echo "❌ Failed to install dependencies. Please check the error messages above."
    exit 1
fi
