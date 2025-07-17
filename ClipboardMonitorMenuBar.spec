# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['menu_bar_app.py'],
    pathex=[],
    binaries=[],
    datas=[('unified_memory_dashboard.py', '.'), ('memory_monitoring_dashboard.py', '.'), ('memory_visualizer.py', '.'), ('modules', 'modules'), ('config.json', '.'), ('constants.py', '.'), ('config_manager.py', '.'), ('utils.py', '.'), ('clipboard_reader.py', '.'), ('module_manager.py', '.'), ('history_viewer.py', '.'), ('web_history_viewer.py', '.'), ('cli_history_viewer.py', '.'), ('com.clipboardmonitor.plist', '.'), ('com.clipboardmonitor.menubar.plist', '.'), ('icon-windowed.icns', '.')],
    hiddenimports=['Cocoa', 'modules.code_formatter_module', 'modules.drawio_module', 'modules.markdown_module', 'modules.mermaid_module'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ClipboardMonitorMenuBar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ClipboardMonitorMenuBar',
)
app = BUNDLE(
    coll,
    name='ClipboardMonitorMenuBar.app',
    icon=None,
    bundle_identifier=None,
)
