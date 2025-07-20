#!/bin/bash

# Test PKG Installation Script
# Tests the PKG installer functionality

set -e

echo "🧪 Testing PKG Installation"
echo "=========================="

# Check if PKG exists
if [ ! -f "ClipboardMonitor-1.0.pkg" ]; then
    echo "❌ PKG file not found. Building first..."
    ./build_create_install_pkg.sh
fi

echo "✅ PKG file found: ClipboardMonitor-1.0.pkg"

# Test PKG info
echo ""
echo "📋 PKG Information:"
pkgutil --payload-files ClipboardMonitor-1.0.pkg | head -10

echo ""
echo "📦 PKG Contents:"
pkgutil --files ClipboardMonitor-1.0.pkg | head -10

echo ""
echo "🎯 PKG is ready for installation!"
echo "To install: sudo installer -pkg ClipboardMonitor-1.0.pkg -target /"
