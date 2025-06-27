# Clipboard Monitor - Agent Guidelines

## Commands
- **Test**: `python3 tests/run_comprehensive_tests.py` (run all tests)
- **Single Test**: `python3 -m unittest tests.test_<module>` (run individual test file)
- **Install Dependencies**: `./install_dependencies.sh`
- **Start Main Service**: `python3 main.py`
- **Start Menu Bar App**: `python3 menu_bar_app.py`
- **Format/Lint**: No specific formatter configured - follow existing code style

## Architecture
This is a macOS clipboard monitoring application with modular processing:
- **main.py**: Core clipboard monitor with enhanced (pyobjc) and polling modes
- **modules/**: Processing modules (history, markdown, mermaid, code formatter)
- **menu_bar_app.py**: Menu bar interface using rumps
- **history_viewer.py**: GUI for viewing clipboard history
- **config.json**: Module enabling/configuration
- **utils.py**: Shared utilities for paths, logging, notifications

## Code Style
- Python 3 standard conventions
- Use logging module for output (`logger.info()`, `logger.error()`)
- Import from utils for shared functionality (paths, notifications)
- Module interface: `process(clipboard_content, config)` function required
- Configuration through config.json with section-based structure
- Use `safe_expanduser()` for path handling with tildes
- Threading locks for clipboard processing to prevent race conditions
