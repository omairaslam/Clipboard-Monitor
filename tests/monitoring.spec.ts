import { test, expect } from '@playwright/test';

// Toggles advanced monitoring via the UI and checks the badge state updates

test('advanced monitoring toggle updates badge', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));

  await page.goto('http://localhost:8001/', { waitUntil: 'load' });

  // Make sure toggle button is present
  const toggleBtn = page.locator('#monitoringToggleBtn');
  await expect(toggleBtn).toHaveCount(1);

  // Read current badge state
  const badge = page.locator('#advanced-status');
  await expect(badge).toHaveCount(1);
  const beforeText = (await badge.textContent())?.trim() || '';

  // Scroll into view and click toggle
  await toggleBtn.scrollIntoViewIfNeeded();
  await toggleBtn.click();

  // Wait for badge text to change
  await expect(badge).not.toHaveText(beforeText, { timeout: 12000 });

  // Click toggle back to restore state
  await toggleBtn.scrollIntoViewIfNeeded();
  await toggleBtn.click();
  await expect(badge).toHaveText(beforeText, { timeout: 12000 });

  // Fail if page errors occurred
  if (errors.length) throw new Error('Page error: ' + errors[0]);
});

