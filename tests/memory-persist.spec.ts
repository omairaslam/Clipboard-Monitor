import { test, expect } from '@playwright/test';

// Phase 2: Verify persisted state (umc_mode, umc_live_range) across reloads

test('memory chart persists mode and live range across reload', async ({ page, context }) => {
  const url = 'http://localhost:8001/';
  await page.goto(url, { waitUntil: 'load' });

  // Set live range to 2h
  const liveRange = page.locator('#live-range-select');
  await liveRange.selectOption('2h');
  await expect(page.locator('#mode-badge')).toHaveText('Live');

  // Switch to historical to flip mode, then back to live before reload
  await page.locator('#historical-btn').click();
  await page.locator('#historical-options').waitFor();
  await page.locator('#realtime-btn').click();

  // Reload
  await page.reload({ waitUntil: 'load' });

  // Expect persisted live mode and 2h range
  await expect(page.locator('#mode-badge')).toHaveText('Live');
  await expect(page.locator('#live-range-select')).toHaveValue('2h');
});

