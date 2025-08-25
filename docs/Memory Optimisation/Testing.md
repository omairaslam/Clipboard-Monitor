# Testing and Reports

This doc explains how to run the automated UI tests (Playwright) and view HTML reports.

## Prerequisites
- Node.js 18+
- Repo opened at root (playwright.config.ts present)

## Run tests

Option A: VS Code buttons (recommended)
- Click `🧪 Playwright` to run the full suite and auto-open report
- Click `📊 Report` to open the last report

Option B: VS Code Tasks
- Command Palette → `Tasks: Run Task` → choose:
  - `🧪 Playwright: Run Suite`
  - `📊 Playwright: Show Report`

Option C: CLI
- `npx playwright test`
- `npx playwright show-report`

## Report & diagnostics
- HTML report output: `playwright-report/index.html`
- Retries: `1`, with `trace: on-first-retry`
- Web server: auto-starts `unified_memory_dashboard.py` on port 8001

## Test coverage (high level)
- Dashboard smoke: page loads without script errors; header elements render
- Monitoring toggle: badge flips and reverts; status wired to `/api/current`
- Monitoring points: `#advanced-data-points` increments while active
- Memory modes/ranges: live ranges (2h, 4h), historical (24h), and `all` with confirmation
- Resolution switching: minute/full/10sec/hour smooth transitions, canvas stays present
- Transitions stress: Live ↔ Historical stability across repeated switches
- Persistence: `umc_mode` + `umc_live_range` restored after reload

## Performance sentinel
- `tests/perf-resolution.spec.ts` measures how long the chart title takes to settle after a resolution switch
- Soft threshold: 1500ms (warns in console if exceeded; does not fail tests)

## MCP (Augment) notes
- If MCP runner is enabled in your Augment build, run the Playwright tool from Integrations/MCP or the Command Palette
- If not visible, use the VS Code Tasks/buttons above

