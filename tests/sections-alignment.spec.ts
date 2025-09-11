import { test, expect } from '@playwright/test';

const TOL = 2; // px

function approxEq(a: number, b: number, tol = TOL) { return Math.abs(a - b) <= tol; }

async function bbox(page, selector: string) {
  const el = page.locator(selector).first();
  await expect(el).toBeVisible();
  const box = await el.boundingBox();
  if (!box) throw new Error(`No box for ${selector}`);
  return box;
}

test.describe('Major sections alignment (Dashboard)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('Header, nav, and charts have equal width, aligned edges, and equal vertical gaps', async ({ page }) => {
    const header = await bbox(page, '#top-header');
    const nav = await bbox(page, '.nav-shell');

    const charts = page.locator('#dashboard-tab .chart-container');
    await expect(charts).toHaveCount(2);
    const b0 = await charts.nth(0).boundingBox();
    const b1 = await charts.nth(1).boundingBox();
    if (!b0 || !b1) throw new Error('Charts not visible');

    // Debug widths
    console.log('Widths:', { header: header.width, nav: nav.width, chart1: b0.width, chart2: b1.width });
    console.log('Lefts:', { header: header.x, nav: nav.x, chart1: b0.x, chart2: b1.x });

    // Equal widths and edges
    const widths = [header.width, nav.width, b0.width, b1.width];
    expect(approxEq(widths[0], widths[1])).toBeTruthy();
    expect(approxEq(widths[1], widths[2])).toBeTruthy();
    expect(approxEq(widths[2], widths[3])).toBeTruthy();

    const lefts = [header.x, nav.x, b0.x, b1.x];
    expect(approxEq(lefts[0], lefts[1])).toBeTruthy();
    expect(approxEq(lefts[1], lefts[2])).toBeTruthy();
    expect(approxEq(lefts[2], lefts[3])).toBeTruthy();

    const rights = [header.x + header.width, nav.x + nav.width, b0.x + b0.width, b1.x + b1.width];
    expect(approxEq(rights[0], rights[1])).toBeTruthy();
    expect(approxEq(rights[1], rights[2])).toBeTruthy();
    expect(approxEq(rights[2], rights[3])).toBeTruthy();

    // Equal vertical gaps between adjacent sections (relative equality, not absolute value)
    const gap1 = nav.y - (header.y + header.height);
    const gap2 = b0.y - (nav.y + nav.height);
    const gap3 = b1.y - (b0.y + b0.height);

    console.log('Gaps:', { gap1, gap2, gap3 });

    expect(approxEq(gap1, gap2, 2)).toBeTruthy();
    expect(approxEq(gap2, gap3, 2)).toBeTruthy();
  });
});

test.describe('Major sections alignment (Analysis & Controls)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByText('Analysis & Controls').click();
  });

  test('top note card and following cards align with nav (edges and width)', async ({ page }) => {
    const nav = await bbox(page, '.nav-shell');

    // first meaningful white block is the green info band container (.card within analysis)
    const firstCard = await bbox(page, '#analysis-tab > .card');

    // Ensure equal width and edges with nav
    expect(approxEq(nav.width, firstCard.width)).toBeTruthy();
    expect(approxEq(nav.x, firstCard.x)).toBeTruthy();
    expect(approxEq(nav.x + nav.width, firstCard.x + firstCard.width)).toBeTruthy();

    // Next block (Monitoring Controls .card)
    const secondCard = await bbox(page, '#analysis-tab > .card + .card');

    // Edges and width alignment
    expect(approxEq(secondCard.width, firstCard.width)).toBeTruthy();
    expect(approxEq(secondCard.x, firstCard.x)).toBeTruthy();
    expect(approxEq(secondCard.x + secondCard.width, firstCard.x + firstCard.width)).toBeTruthy();
  });
});

test.describe('Major sections alignment (Clipboard History)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByText('Clipboard History').click();
  });

  test('first content block aligns with nav (edges and width)', async ({ page }) => {
    const nav = await bbox(page, '.nav-shell');
    const firstBlock = await bbox(page, '#clipboard-tab > *');

    expect(approxEq(nav.width, firstBlock.width)).toBeTruthy();
    expect(approxEq(nav.x, firstBlock.x)).toBeTruthy();
    expect(approxEq(nav.x + nav.width, firstBlock.x + firstBlock.width)).toBeTruthy();
  });
});

