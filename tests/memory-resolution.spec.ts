import { test, expect } from '@playwright/test';

// Phase 2: Verify changing historical resolution updates UI without errors

test('historical resolution changes are smooth and error-free', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));

  await page.goto('http://localhost:8001/', { waitUntil: 'load' });

  // Open Historical options
  const historicalBtn = page.locator('#historical-btn');
  await historicalBtn.click();
  await expect(page.locator('#historical-options')).toBeVisible();

  // Select a bounded historical range (24 hours)
  const histRange = page.locator('#historical-range');
  await histRange.selectOption('24');

  // Resolution selector should exist
  const resSelect = page.locator('#resolution-select');
  await expect(resSelect).toHaveCount(1);

  const title = page.locator('#chart-title');

  // Switch to minute resolution
  await resSelect.selectOption('minute');
  await expect(title).toHaveText(/Historical Memory Usage/, { timeout: 15000 });

  // Switch to full resolution
  await resSelect.selectOption('full');
  await expect(title).toHaveText(/Historical Memory Usage/, { timeout: 15000 });

  // Switch to 10s resolution
  await resSelect.selectOption('10sec');
  await expect(title).toHaveText(/Historical Memory Usage/, { timeout: 15000 });

  // Switch to hour resolution
  await resSelect.selectOption('hour');
  await expect(title).toHaveText(/Historical Memory Usage/, { timeout: 15000 });

  // Chart canvas must remain present/visible
  await expect(page.locator('#memoryChart')).toBeVisible();

  if (errors.length) throw new Error('Page error: ' + errors[0]);
});

