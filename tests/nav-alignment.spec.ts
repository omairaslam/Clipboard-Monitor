import { test, expect } from '@playwright/test';

// Validate the navigation tabs and controls are aligned and spaced consistently
// across normal and collapsed states. This focuses on visual geometry using
// bounding boxes and allows a small tolerance for sub‑pixel rendering.

const TOL = 2; // pixels tolerance (tight alignment)

function centerY(box: { y: number; height: number }) {
  return box.y + box.height / 2;
}

async function getBox(el: import('@playwright/test').Locator) {
  const box = await el.boundingBox();
  if (!box) throw new Error('Element not visible: ' + (await el.first().evaluate((e: Element) => e.outerHTML)));
  return box;
}

test.describe('Nav shell alignment', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/', { waitUntil: 'load' });
  });

  test('tabs have equal widths and are vertically aligned with controls', async ({ page }) => {
    const navShell = page.locator('#nav-shell');
    const tabs = navShell.locator('.tabs');
    const controls = navShell.locator('.nav-controls');
    const tabEls = [
      tabs.locator('.tab').nth(0),
      tabs.locator('.tab').nth(1),
      tabs.locator('.tab').nth(2),
    ];

    // Wait for layout
    await expect(tabs).toBeVisible();
    await expect(controls).toBeVisible();

    const [bTabs, bCtrls, b1, b2, b3] = await Promise.all([
      getBox(tabs),
      getBox(controls),
      getBox(tabEls[0]),
      getBox(tabEls[1]),
      getBox(tabEls[2]),
    ]);

    // Tabs and controls should be vertically centered along same row
    expect(Math.abs(centerY(bTabs) - centerY(bCtrls))).toBeLessThanOrEqual(TOL);

    // Each tab should have approximately equal width
    expect(Math.abs(b1.width - b2.width)).toBeLessThanOrEqual(TOL);
    expect(Math.abs(b2.width - b3.width)).toBeLessThanOrEqual(TOL);

    // Tabs should span the left side; controls anchored to right side (no overlap)
    expect(b1.x).toBeGreaterThanOrEqual(bTabs.x - TOL);
    expect(bCtrls.x).toBeGreaterThan(b3.x + b3.width - 10); // controls to the right of last tab
  });

  test('collapsed strip aligns with controls and full width', async ({ page }) => {
    const navShell = page.locator('#nav-shell');
    const collapseBtn = page.locator('#nav-collapse-toggle');

    await expect(collapseBtn).toBeVisible();
    await collapseBtn.click();

    const strip = navShell.locator('.collapse-strip');
    const controls = navShell.locator('.nav-controls');

    await expect(strip).toBeVisible();
    await expect(controls).toBeVisible();

    const [bStrip, bCtrls] = await Promise.all([getBox(strip), getBox(controls)]);

    // Still on same row vertically
    expect(Math.abs(centerY(bStrip) - centerY(bCtrls))).toBeLessThanOrEqual(TOL);

    // Strip should start near container left; controls flush to the right of it
    expect(bCtrls.x).toBeGreaterThanOrEqual(bStrip.x + bStrip.width - 40);
  });

  test('container edges and heights are consistent', async ({ page }) => {
    const container = page.locator('.container');
    const navShell = page.locator('#nav-shell');
    const tabs = navShell.locator('.tabs');
    const controls = navShell.locator('.nav-controls');

    await Promise.all([
      expect(container).toBeVisible(),
      expect(navShell).toBeVisible(),
      expect(tabs).toBeVisible(),
      expect(controls).toBeVisible(),
    ]);

    const [bCont, bShell, bTabs, bCtrls] = await Promise.all([
      getBox(container), getBox(navShell), getBox(tabs), getBox(controls)
    ]);

    // Shell edges align with container
    expect(Math.abs(bShell.x - bCont.x)).toBeLessThanOrEqual(TOL);
    expect(Math.abs((bShell.x + bShell.width) - (bCont.x + bCont.width))).toBeLessThanOrEqual(TOL);

    // Left and right content alignment within shell
    expect(Math.abs(bTabs.x - bCont.x)).toBeLessThanOrEqual(TOL);
    expect(Math.abs((bCtrls.x + bCtrls.width) - (bCont.x + bCont.width))).toBeLessThanOrEqual(TOL);

    // Heights of row participants are equal (±1px)
    const hTol = 1;
    expect(Math.abs(bTabs.height - 44)).toBeLessThanOrEqual(hTol);
    expect(Math.abs(bCtrls.height - 44)).toBeLessThanOrEqual(hTol);
  });

  test('header collapse preserves nav alignment', async ({ page }) => {
    const navShell = page.locator('#nav-shell');
    const tabs = navShell.locator('.tabs');
    const controls = navShell.locator('.nav-controls');

    // Collapse header
    const hdrCollapse = page.locator('#header-collapse-toggle');
    await expect(hdrCollapse).toBeVisible();
    await hdrCollapse.click();

    const [bTabs, bCtrls] = await Promise.all([getBox(tabs), getBox(controls)]);
    expect(Math.abs(centerY(bTabs) - centerY(bCtrls))).toBeLessThanOrEqual(TOL);
  });

  test('no console errors during initial render', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });
    await page.reload();
    await page.waitForLoadState('load');
    const filtered = errors.filter(e => !/Failed to fetch|Error fetching memory data|Error loading analysis data/i.test(e));
    expect(filtered.join('\n')).toBe('');
  });

  test('responsive widths keep alignment', async ({ page }) => {
    for (const width of [1400, 1100, 900]) {
      await page.setViewportSize({ width, height: 800 });
      const navShell = page.locator('#nav-shell');
      const tabs = navShell.locator('.tabs');
      const controls = navShell.locator('.nav-controls');
      const [bTabs, bCtrls] = await Promise.all([getBox(tabs), getBox(controls)]);
      expect(Math.abs(centerY(bTabs) - centerY(bCtrls))).toBeLessThanOrEqual(TOL);
    }
  });
});

