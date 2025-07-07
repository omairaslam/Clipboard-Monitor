#!/bin/bash

set -e

# Clean previous builds
rm -rf build dist

# Create app bundle
python3 setup.py py2app

# Define paths
APP_NAME="Clipboard Monitor"
SOURCE_APP_NAME="menu_bar_app"
VERSION="1.0"
DMG_NAME="ClipboardMonitor-$VERSION.dmg"
VOL_NAME="$APP_NAME Installer"
SOURCE_DIR="dist"
TARGET_DIR="dmg"

# Create DMG structure
mkdir -p "$TARGET_DIR"
mv "$SOURCE_DIR/$SOURCE_APP_NAME.app" "$TARGET_DIR/$APP_NAME.app"
cp install.sh "$TARGET_DIR/"

# Create DMG
hdiutil create -volname "$VOL_NAME" -srcfolder "$TARGET_DIR" -ov -format UDZO "$DMG_NAME"

# Clean up
rm -rf "$TARGET_DIR"

echo "DMG created: $DMG_NAME"