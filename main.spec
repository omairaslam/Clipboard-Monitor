# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Clipboard Monitor main service
This creates a standalone executable for the background clipboard monitoring service
"""

import os
import sys
from pathlib import Path

# Get the current directory (where this spec file is located)
spec_root = os.path.dirname(os.path.abspath(SPEC))

# Define data files to include
datas = [
    # Configuration and template files
    (os.path.join(spec_root, 'config.json'), '.'),
    (os.path.join(spec_root, 'plist_files', 'com.clipboardmonitor.plist'), '.'),
    (os.path.join(spec_root, 'plist_files', 'com.clipboardmonitor.menubar.plist'), '.'),
    
    # Python modules that need to be accessible as files
    (os.path.join(spec_root, 'clipboard_reader.py'), '.'),
    (os.path.join(spec_root, 'module_manager.py'), '.'),
    (os.path.join(spec_root, 'config_manager.py'), '.'),
    (os.path.join(spec_root, 'constants.py'), '.'),
    (os.path.join(spec_root, 'utils.py'), '.'),
    
    # Modules directory - include all Python files
    (os.path.join(spec_root, 'modules'), 'modules'),
    
    # Additional Python files that might be called via subprocess
    (os.path.join(spec_root, 'web_history_viewer.py'), '.'),
    (os.path.join(spec_root, 'cli_history_viewer.py'), '.'),
    (os.path.join(spec_root, 'history_viewer.py'), '.'),
]

# Hidden imports - modules that PyInstaller might not detect automatically
hiddenimports = [
    # Core dependencies
    'pyperclip',
    'rumps',
    'psutil',
    
    # macOS frameworks
    'objc',
    'AppKit',
    'Foundation',
    'CoreFoundation',
    'Cocoa',
    
    # Standard library modules that might be imported dynamically
    'importlib',
    'importlib.util',
    'threading',
    'logging',
    'pathlib',
    'json',
    'subprocess',
    're',
    'tracemalloc',
    'datetime',
    'webbrowser',
    'time',
    'sys',
    'os',
    
    # Modules from the modules directory
    'modules',
    'modules.code_formatter_module',
    'modules.drawio_module', 
    'modules.history_module',
    'modules.markdown_module',
    'modules.mermaid_module',
    
    # PyObjC specific imports
    'PyObjCTools',
    'PyObjCTools.AppHelper',
]

# Binaries - any additional binary files needed
binaries = []

# Analysis configuration
a = Analysis(
    ['main.py'],
    pathex=[spec_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude deprecated or problematic modules
        'Carbon',
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# PYZ archive
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ClipboardMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# COLLECT - gather all files for distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ClipboardMonitor',
)

# Bundle configuration for macOS app
app = BUNDLE(
    coll,
    name='ClipboardMonitor.app',
    icon=None,  # Add icon path here if you have one
    bundle_identifier='com.clipboardmonitor.main',
    version='1.0.0',
    info_plist={
        'CFBundleName': 'Clipboard Monitor Service',
        'CFBundleDisplayName': 'Clipboard Monitor Service',
        'CFBundleIdentifier': 'com.clipboardmonitor.main',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,  # Background service - no dock icon
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': 'Copyright © 2025 Clipboard Monitor',
        'LSBackgroundOnly': True,  # Background only service
    },
)
