import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'tests',
  reporter: [['html', { outputFolder: 'playwright-report', open: 'never' }], ['list']],
  retries: 1,
  use: {
    headless: true,
    baseURL: 'http://localhost:8001',
    ignoreHTTPSErrors: true,
    viewport: { width: 1280, height: 800 },
    trace: 'on-first-retry',
  },
  timeout: 60000,
  workers: 1,
  webServer: {
    command: 'python3 unified_memory_dashboard.py --port 8001',
    port: 8001,
    timeout: 60_000,
    reuseExistingServer: true,
  },
});

