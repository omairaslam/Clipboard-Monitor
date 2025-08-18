# Unified Dashboard Cleanup Plan

This document outlines a safe, staged plan to clean up the unified memory dashboard and related project areas without breaking functionality.

## Objectives
- Preserve behavior and API shape while improving structure
- Reduce risk through small, incremental changes
- Consolidate documentation and remove stray artifacts
- Modularize the monolithic dashboard file
- Introduce minimal validation tests to prevent regressions

## Current Issues (Summary)
- Monolithic `unified_memory_dashboard.py` mixing server, data collection, frontend, and analysis
- Stray/historical fix summaries and logs in repo root
- Duplicative logic across memory collection functions
- Frontend JS/CSS inline within Python template
- Docs partially organized; many historical notes not consolidated

## Phased Plan

### Phase 1: Organize and Move (No behavior change)
- Create `dashboard/` package and split modules:
  - `dashboard/server.py` – HTTP server + routes
  - `dashboard/data.py` – memory/process/system data functions
  - `dashboard/analysis.py` – AdvancedMemoryLeakDetector + helpers
  - `dashboard/template.py` or `templates/index.html` – UI template
  - `dashboard/utils_psutil.py` – psutil import workarounds
- Keep `unified_memory_dashboard.py` as a thin entrypoint importing these modules.
- Move stray root docs into `docs/History/` (see Consolidation below).

Safety: Files moved and imports adjusted only. Verify dashboard runs and endpoints respond.

### Phase 2: De-duplicate and Clarify Logic
- Create a single `classify_process(proc_info)` and reuse everywhere.
- Make `get_memory_data()` the single source of truth; avoid recomputation.
- Optional: short-lived cache (e.g., 200ms) to avoid repeated psutil scans per request burst.

Safety: Pure refactor; validate endpoint payload shapes before/after.

### Phase 3: Frontend Extraction (No functional change)
- Move inline CSS/JS to `static/style.css` and `static/app.js`.
- Keep DOM IDs and endpoints identical.
- Document optional UI IDs and continue silencing missing-element warnings.

### Phase 4: Documentation Consolidation
- Add `docs/Architecture/`:
  - `Dashboard.md` – module layout, endpoints, data flow
  - `ProcessDetection.md` – script vs PyInstaller detection
- Add `docs/Operations/`:
  - `BuildAndPackaging.md` – PKG flow; mark DMG as deprecated
  - `Troubleshooting.md` – psutil, multiple instances, ports
- Move historical notes to `docs/History/`:
  - `UNIFIED_DASHBOARD_FIX_SUMMARY.md`
  - `UNIFIED_DASHBOARD_MEMORY_FIX_SUMMARY.md`
  - `INSTALL_SCRIPT_IMPROVEMENTS_SUMMARY.md`
  - `MERMAID_THEME_ISSUES_LOG.md`
- Update `docs/INDEX.md` to link to the above.

### Phase 5: Minimal Tests/Validation
- `tests/test_process_detection.py` – unit test for `classify_process()`
- `tests/test_endpoints.py` – starts server in thread; asserts `/api/current`, `/api/memory` payload shape
- Add a simple `make test` or `python -m pytest` note in docs

## Risk Mitigation
- Execute phases as small PRs:
  1) Extract `utils_psutil.py`; import and verify
  2) Extract `data.py`; verify `/api/current`, `/api/system`, `/api/processes`
  3) Extract `analysis.py`
  4) Extract HTML template to `templates/index.html`
  5) Move docs; update index
- After each PR, run dashboard, hit endpoints, verify charts render

## Optional Performance Improvements (Non-breaking)
- Micro-cache results of psutil sampling within a short window
- Consider async sampling in background if future load increases

## Expected Outcomes
- Cleaner, modular codebase with clear separation of concerns
- Easier maintenance and future enhancements (e.g., WebSockets)
- Documentation that reflects current and historical context
- Reduced risk of regressions via minimal tests

## Status
Draft plan prepared for execution. Recommend starting with Phase 1 (module extraction) when ready.

