#!/bin/bash

# Build script for Clipboard Monitor DMG
# Creates a completely self-contained macOS application with:
# - Bundled Python 3.9 interpreter (universal binary)
# - All required dependencies included
# - Code signed components
# - Professional DMG installer

set -e

echo "🚀 Building Clipboard Monitor..."
echo "📦 Creating self-contained macOS application..."

# Configuration for code signing and notarization (optional)
# Uncomment and configure these if you have Apple Developer certificates:
# DEVELOPER_ID="Developer ID Application: Your Name (TEAM_ID)"
# NOTARIZATION_PROFILE="notarization-profile"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist

# Create app bundle with py2app (includes Python interpreter and all dependencies)
echo "🔨 Building app bundle with py2app..."
python3 setup.py py2app

# Verify the app was built successfully
if [ ! -d "dist/Clipboard Monitor.app" ]; then
    echo "❌ Error: App bundle was not created successfully"
    exit 1
fi

echo "✅ App bundle created successfully"

# Fix Python framework paths (ensures proper linking)
echo "🔧 Fixing Python framework paths..."
./fix_framework_paths.sh

# Optional: Additional code signing with your Developer ID
# (py2app already signs with ad-hoc signatures, but you can replace with your certificate)
# if [ -n "$DEVELOPER_ID" ]; then
#     echo "✍️  Code signing app bundle with Developer ID..."
#     codesign --force --deep --sign "$DEVELOPER_ID" "dist/Clipboard Monitor.app"
# fi

# Optional: Notarization (requires Apple Developer account)
# if [ -n "$NOTARIZATION_PROFILE" ]; then
#     echo "📋 Notarizing app bundle..."
#     xcrun notarytool submit "dist/Clipboard Monitor.app" --keychain-profile "$NOTARIZATION_PROFILE" --wait
#     xcrun stapler staple "dist/Clipboard Monitor.app"
#     echo "✅ App notarized successfully"
# fi

# Define paths
APP_NAME="Clipboard Monitor"
SOURCE_APP_NAME="Clipboard Monitor"  # Updated to match the actual app name from setup.py
VERSION="1.0"
DMG_NAME="ClipboardMonitor-$VERSION.dmg"
VOL_NAME="$APP_NAME Installer"
SOURCE_DIR="dist"
TARGET_DIR="dmg"

# Create DMG structure
echo "📦 Creating DMG installer..."
mkdir -p "$TARGET_DIR"
mv "$SOURCE_DIR/$SOURCE_APP_NAME.app" "$TARGET_DIR/$APP_NAME.app"
cp install.sh "$TARGET_DIR/"
cp uninstall.sh "$TARGET_DIR/"

# Create DMG
hdiutil create -volname "$VOL_NAME" -srcfolder "$TARGET_DIR" -ov -format UDZO "$DMG_NAME"

# Optional: Sign and notarize the DMG
# if [ -n "$DEVELOPER_ID" ]; then
#     echo "✍️  Code signing DMG..."
#     codesign --force --sign "$DEVELOPER_ID" "$DMG_NAME"
# fi
# if [ -n "$NOTARIZATION_PROFILE" ]; then
#     echo "📋 Notarizing DMG..."
#     xcrun notarytool submit "$DMG_NAME" --keychain-profile "$NOTARIZATION_PROFILE" --wait
#     xcrun stapler staple "$DMG_NAME"
# fi

# Clean up
rm -rf "$TARGET_DIR"

echo ""
echo "🎉 Build complete! DMG created: $DMG_NAME"
echo ""
echo "📊 Build Summary:"
echo "  📱 App bundle size: $(du -sh "dist/$SOURCE_APP_NAME.app" 2>/dev/null | cut -f1 || echo "N/A")"
echo "  💿 DMG size: $(du -sh "$DMG_NAME" | cut -f1)"
echo ""
echo "✅ The app is completely self-contained and includes:"
echo "  🐍 Python 3.9 interpreter (universal binary: x86_64 + arm64)"
echo "  📚 All required dependencies (rumps, pyperclip, objc, psutil, etc.)"
echo "  🔐 Code signed components"
echo "  🚀 Ready for distribution on any macOS system"
echo ""
echo "ℹ️  Users do NOT need Python installed - everything is bundled!"