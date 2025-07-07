# DMG Details

This document provides details about the `ClipboardMonitor-1.0.dmg` file and the installation process.

## Contents

The DMG file contains two items:

1.  **Clipboard Monitor.app**: The main application bundle.
2.  **install.sh**: An installation script that automates the setup process.

## Installation Process

The `install.sh` script performs the following actions:

1.  **Creates Directories**: It creates the necessary directories for logs and launch agents (`~/Library/Logs` and `~/Library/LaunchAgents`).
2.  **Unloads Existing Services**: It unloads any existing versions of the Clipboard Monitor services to ensure a clean installation.
3.  **Generates Plist Files**: It dynamically generates the `com.omairaslam.clipboardmonitor.plist` and `com.omairaslam.clipboardmonitor.menubar.plist` files with the correct paths for the user's system.
4.  **Loads Services**: It loads the newly created plist files, starting the background and menubar services.

## Path Configuration

The `install.sh` script handles all path configurations automatically. The user does not need to manually edit any files. The script uses the `$HOME` environment variable to determine the correct paths for the current user.