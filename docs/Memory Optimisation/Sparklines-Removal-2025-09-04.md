# Sparklines Removal — 2025-09-04

Summary
- The Trend Explorer sparklines feature was removed from the Unified Memory Dashboard due to extended instability and repeated regressions.
- All sparklines scripts and tests were deleted; the HTML container remains for potential future, non-sparkline content.

Changes
- Removed script loading and bootstrapping for sparklines in the dashboard HTML.
- Deleted static/js/trend-explorer.js and static/js/spark-tooltips.js.
- Removed all Playwright tests for sparklines.
- Stripped any dashboard.js calls to __module_updateTrendExplorer.

Rationale
- Several attempts to stabilize SVG/canvas rendering and tooltips led to brittle behavior. To restore reliability and velocity, we removed the feature entirely.

Follow-ups
- If a trend visualization is needed later, consider a minimal canvas-only line renderer behind a feature flag, with dedicated Playwright smoke tests.
- Keep documentation in sync by updating docs/Memory Optimisation/INDEX.md with this entry.

Audit trail
- Branch: hotfix/restore-sparklines
- Merged and pushed removal commits to main on 2025-09-04.

