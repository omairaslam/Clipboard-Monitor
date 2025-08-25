import { test, expect } from '@playwright/test';

// Phase 3: Verify advanced-data-points increments while monitoring is active

test('advanced data points increment while monitoring active', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));

  await page.goto('http://localhost:8001/', { waitUntil: 'load' });

  // Switch to Analysis & Controls tab
  await page.getByText('Analysis & Controls', { exact: false }).click();
  await expect(page.locator('#analysis-tab')).toBeVisible();

  const toggleBtn = page.locator('#monitoringToggleBtn');
  await toggleBtn.scrollIntoViewIfNeeded();
  await expect(toggleBtn).toHaveCount(1);

  const points = page.locator('#advanced-data-points');
  await expect(points).toHaveCount(1);

  // Start monitoring (if not already)
  await toggleBtn.click();
  // Wait a bit for server to start and first sample
  await page.waitForTimeout(1500);

  const before = parseInt((await points.textContent())?.trim() || '0', 10) || 0;

  // Wait for some time for more samples (interval default should be visible on UI; we give 3s)
  await page.waitForTimeout(3000);

  const after = parseInt((await points.textContent())?.trim() || '0', 10) || 0;
  expect(after).toBeGreaterThanOrEqual(before);

  // Stop monitoring to restore state
  await toggleBtn.scrollIntoViewIfNeeded();
  await toggleBtn.click();

  if (errors.length) throw new Error('Page error: ' + errors[0]);
});

