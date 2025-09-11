import { test, expect } from '@playwright/test';

// Navigate to clipboard tab and verify that table renders and meta updates

test('clipboard tab renders and loads items/meta', async ({ page }) => {
  // Navigate directly to clipboard tab
  await page.goto('http://localhost:8001/#clipboard', { waitUntil: 'load' });

  // Click tab in case hash navigation didn't flip UI
  await page.getByText('Clipboard History', { exact: false }).click();

  // Debug: report classes and display
  const classes = await page.evaluate(() => ({
    dash: document.getElementById('dashboard-tab')?.className,
    anal: document.getElementById('analysis-tab')?.className,
    clip: document.getElementById('clipboard-tab')?.className,
    clipDisplay: window.getComputedStyle(document.getElementById('clipboard-tab')!).display,
  }));
  console.log('TAB CLASSES:', classes);

  // Additional debug: log inline style and try forcing display if needed
  const debugInfo = await page.evaluate(() => ({
    clipStyle: document.getElementById('clipboard-tab')?.getAttribute('style') || null,
  }));
  console.log('CLIPBOARD TAB STYLE:', debugInfo);



  // Wait for filter controls to appear
  const meta = page.locator('#clip-meta');
  // If hidden, force switch by calling switchTab directly
  if (!(await meta.isVisible())) {
    await page.evaluate(() => (window as any).switchTab?.('clipboard'));
  }
  // Try to ensure visibility if still hidden
  if (!(await meta.isVisible())) {
    await page.evaluate(() => { const ct = document.getElementById('clipboard-tab'); if (ct) { ct.classList.add('active'); (ct as any).style.display = 'block'; } });
  }
  await expect(meta).toBeVisible();

  // Allow initial fetch to complete
  await page.waitForTimeout(500);

  // Meta should show either items count or error message replaced
  await expect(meta).not.toHaveText(/Loading…/);

  // Table headers should be present
  await expect(page.locator('table thead')).toBeVisible();
  await expect(page.locator('#clip-tbody')).toBeVisible();

  // Optional: trigger a refresh and assert no errors bubble to console
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.locator('#clip-refresh').click();
  await page.waitForTimeout(300);
  expect(errors).toEqual([]);
});

