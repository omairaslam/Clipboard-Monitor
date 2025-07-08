#!/bin/bash

set -e

# Clean previous builds
rm -rf build dist

# Create app bundle
python3 setup.py py2app

# Define paths
APP_NAME="Clipboard Monitor"
SOURCE_APP_NAME="menu_bar_app" # This is the name py2app gives the .app folder initially
VERSION="1.0" # Consider making this dynamic or passed as an argument
DMG_NAME="ClipboardMonitor-$VERSION.dmg"
VOL_NAME="$APP_NAME" # Volume name when DMG is mounted
FINAL_APP_NAME="$APP_NAME.app" # Final name of the .app in the DMG

SOURCE_APP_PATH="$SOURCE_DIR/$SOURCE_APP_NAME.app"
STAGING_DIR="dmg_staging" # Temporary directory for DMG contents

# Clean up previous staging directory if it exists
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

# Move the generated .app to the staging directory with the final desired name
mv "$SOURCE_APP_PATH" "$STAGING_DIR/$FINAL_APP_NAME"

# Create a symbolic link to the Applications folder
ln -s /Applications "$STAGING_DIR/Applications"

echo "Creating DMG..."
hdiutil create \
    -volname "$VOL_NAME" \
    -srcfolder "$STAGING_DIR" \
    -ov \
    -fs HFS+ \
    -format UDZO \
    "$DMG_NAME"

# Clean up staging directory
rm -rf "$STAGING_DIR"

echo "DMG created successfully: $DMG_NAME"