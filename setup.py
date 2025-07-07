
from setuptools import setup

APP = ['menu_bar_app.py']
DATA_FILES = [
    'main.py',
    'clipboard_reader.py',
    'module_manager.py',
    'config_manager.py',
    'constants.py',
    'utils.py',
    'com.omairaslam.clipboardmonitor.plist',
    'com.omairaslam.clipboardmonitor.menubar.plist',
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
    'argv_emulation': True,
    'packages': ['rumps', 'pyperclip', 'objc']
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
