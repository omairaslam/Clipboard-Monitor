import { test, expect } from '@playwright/test';

// Captures a screenshot of the nav-shell to validate the trailing-gap fix
// and asserts that the tabs row fills the container width within a tight tolerance.
const TOL = 2; // px

function right(box: { x: number; width: number }) { return box.x + box.width; }

async function getBox(el: import('@playwright/test').Locator) {
  const box = await el.boundingBox();
  if (!box) throw new Error('Element not visible');
  return box;
}

test('nav-shell screenshot and width assertion', async ({ page }) => {
  await page.goto('/', { waitUntil: 'load' });
  const container = page.locator('.container');
  const shell = page.locator('#nav-shell');
  const tabs = shell.locator('.tabs');

  await expect(container).toBeVisible();
  await expect(shell).toBeVisible();
  await expect(tabs).toBeVisible();

  const [bCont, bShell, bTabs] = await Promise.all([
    getBox(container), getBox(shell), getBox(tabs)
  ]);

  // Left edges align to container
  expect(Math.abs(bShell.x - bCont.x)).toBeLessThanOrEqual(TOL);
  expect(Math.abs(bTabs.x - bCont.x)).toBeLessThanOrEqual(TOL);

  // Right edges align to container (no trailing gap)
  expect(Math.abs(right(bTabs) - right(bCont))).toBeLessThanOrEqual(TOL);

  // Screenshot for validation
  await shell.screenshot({ path: 'playwright-report/nav-shell.png' });
});

