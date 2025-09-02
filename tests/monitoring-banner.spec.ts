import { test, expect } from '@playwright/test';

// Phase 3: Verify mini live banner reflects monitoring state and countdown

test('mini banner syncs status, points, interval and shows countdown', async ({ page }) => {
  await page.goto('http://localhost:8001/', { waitUntil: 'load' });
  await page.getByText('Analysis & Controls', { exact: false }).click();

  const miniBtn = page.locator('#monitoringToggleBtnMini');
  const points = page.locator('#live-adv-points');
  const statusText = page.locator('#live-status-text');
  const intervalText = page.locator('#live-interval');
  const nextText = page.locator('#live-next');

  // Start monitoring
  await miniBtn.click();
  await expect(statusText).toHaveText(/ACTIVE/);
  await expect(intervalText).toContainText('Every');

  // Wait to allow points to update and countdown to change
  const beforePts = parseInt((await points.textContent())?.trim() || '0', 10) || 0;
  const beforeNext = await nextText.textContent();
  await page.waitForTimeout(2000);
  const afterNext = await nextText.textContent();
  const afterPts = parseInt((await points.textContent())?.trim() || '0', 10) || 0;

  expect(afterNext).not.toBe(beforeNext);
  expect(afterPts).toBeGreaterThanOrEqual(beforePts);

  // Stop monitoring to restore
  await miniBtn.click();
  await expect(statusText).toHaveText(/INACTIVE/);
});

