import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'tests',
  use: {
    headless: true,
    baseURL: 'http://localhost:8001',
    ignoreHTTPSErrors: true,
    viewport: { width: 1280, height: 800 },
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

