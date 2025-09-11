import { test, expect } from '@playwright/test';

// Verify the four header cards are equal width, equally spaced, and equal height
const TOL = 2; // px

function approxEq(a: number, b: number, tol = TOL) {
  return Math.abs(a - b) <= tol;
}

test.describe('Header cards geometry', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/', { waitUntil: 'load' });
  });

  test('equal widths, equal gaps, equal heights', async ({ page }) => {
    // Wait for header grid to render anywhere on the page
    await page.waitForSelector('.header-grid', { state: 'attached', timeout: 10000 });
    const grid = page.locator('.header-grid');
    await expect(grid).toBeVisible();

    const cards = page.locator('.header-grid .header-card');
    await expect(cards).toHaveCount(4);

    const boxes = (await cards.all()).map(async (el) => {
      const box = await el.boundingBox();
      if (!box) throw new Error('Card not visible');
      return box;
    });
    const b = await Promise.all(boxes);

    // Equal widths
    const w = b.map(x => x.width);
    expect(approxEq(w[0], w[1])).toBeTruthy();
    expect(approxEq(w[1], w[2])).toBeTruthy();
    expect(approxEq(w[2], w[3])).toBeTruthy();

    // Equal heights (stretch to tallest)
    const h = b.map(x => x.height);
    const maxH = Math.max(...h);
    for (const hi of h) expect(approxEq(hi, maxH)).toBeTruthy();

    // Equal gaps between cards
    const x = b.map(bb => bb.x);
    const gap1 = x[1] - (x[0] + b[0].width);
    const gap2 = x[2] - (x[1] + b[1].width);
    const gap3 = x[3] - (x[2] + b[2].width);
    const avg = (gap1 + gap2 + gap3) / 3;
    expect(approxEq(gap1, avg)).toBeTruthy();
    expect(approxEq(gap2, avg)).toBeTruthy();
    expect(approxEq(gap3, avg)).toBeTruthy();

    // Gap should be roughly 12px (+/- 2)
    expect(Math.abs(avg - 12)).toBeLessThanOrEqual(2);
  });
});

