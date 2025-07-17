
from setuptools import setup

APP = ['menu_bar_app.py']
DATA_FILES = [
    'main.py',
    'clipboard_reader.py',
    'module_manager.py',
    'config_manager.py',
    'constants.py',
    'utils.py',
    'com.clipboardmonitor.plist',
    'com.clipboardmonitor.menubar.plist',
    ('modules', [
        'modules/__init__.py',
        'modules/code_formatter_module.py',
        'modules/drawio_module.py',
        'modules/history_module.py',
        'modules/markdown_module.py',
        'modules/mermaid_module.py'
    ])
]
OPTIONS = {
    'argv_emulation': False,  # Disable to avoid Carbon framework issues
    'packages': ['rumps', 'pyperclip', 'objc', 'psutil', 'AppKit', 'Foundation', 'CoreFoundation'],
    'semi_standalone': False,  # Force standalone build to include Python framework
    'excludes': ['Carbon'],  # Exclude deprecated Carbon framework
    'strip': False,  # Don't strip symbols to help with debugging
    'optimize': 0,  # No optimization to preserve debugging info
    'plist': {
        'CFBundleName': 'Clipboard Monitor',
        'CFBundleDisplayName': 'Clipboard Monitor',
        'CFBundleIdentifier': 'com.clipboardmonitor.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,  # Background app (no dock icon)
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': 'Copyright © 2025 Clipboard Monitor'
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
