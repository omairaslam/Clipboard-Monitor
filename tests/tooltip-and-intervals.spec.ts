import { test, expect } from '@playwright/test';

// Optional tests: verify tooltip updates on points increment and countdown behavior at 10s/30s intervals

test('points tooltip updates after increment and countdown behaves at 10s', async ({ page }) => {
  await page.goto('http://localhost:8001/', { waitUntil: 'load' });
  await page.getByText('Analysis & Controls', { exact: false }).click();

  const miniBtn = page.locator('#monitoringToggleBtnMini');
  const points = page.locator('#live-adv-points');
  const lastInc = page.locator('#live-last-inc');
  const intervalSel = page.locator('#monitorInterval');
  const nextText = page.locator('#live-next');

  // Try to read last-inc if present; older builds may not include it
  const lastIncCount = await lastInc.count();

  await intervalSel.selectOption('10');
  await miniBtn.click();
  await expect(points).toHaveText(/\d+/);

  if (lastIncCount > 0) {
    const beforeTooltip = await points.getAttribute('title');
    const beforeText = await lastInc.textContent();

    await page.waitForTimeout(3000);
    const afterTooltip = await points.getAttribute('title');
    const afterText = await lastInc.textContent();

    expect(afterTooltip).not.toBe(beforeTooltip);
    expect(afterText).not.toBe(beforeText);
  }

  // Countdown should change within ~2s at 10s interval
  const c1 = await nextText.textContent();
  await page.waitForTimeout(1500);
  const c2 = await nextText.textContent();
  expect(c2).not.toBe(c1);

  // Restore
  await miniBtn.click();
});

  // Restore
  await miniBtn.click();
});

// Quick check at 30s interval for countdown updates

test('countdown changes visually at 30s', async ({ page }) => {
  await page.goto('http://localhost:8001/', { waitUntil: 'load' });
  await page.getByText('Analysis & Controls', { exact: false }).click();

  const miniBtn = page.locator('#monitoringToggleBtnMini');
  const intervalSel = page.locator('#monitorInterval');
  const nextText = page.locator('#live-next');

  await intervalSel.selectOption('30');
  await miniBtn.click();

  const c1 = await nextText.textContent();
  await page.waitForTimeout(1500);
  const c2 = await nextText.textContent();
  expect(c2).not.toBe(c1);

  await miniBtn.click();
});

