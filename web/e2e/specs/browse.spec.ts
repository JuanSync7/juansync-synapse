// FR1 — Browse: /skills lists artifacts, search filters, click → detail page
// with rendered body + frontmatter + EvalPanel.
import { expect, test } from '@playwright/test';

test('lists skills, filters by search, and opens a detail page', async ({ page }) => {
  await page.goto('/skills');

  await expect(page.getByRole('heading', { name: 'Skills', level: 1 })).toBeVisible();

  // Wait for the list to populate (cards are <li> wrapping a link to a detail).
  const cards = page.locator('ul > li').filter({ has: page.locator('a[href^="/artifact/skill/"]') });
  await expect(cards.first()).toBeVisible({ timeout: 15_000 });

  const total = await cards.count();
  expect(total).toBeGreaterThan(0);

  // Capture the first card's slug from its detail href, then search for it.
  const firstHref = await cards.first().locator('a[href^="/artifact/skill/"]').first().getAttribute('href');
  expect(firstHref).toBeTruthy();
  const slug = decodeURIComponent((firstHref as string).split('/').pop() as string);

  const search = page.getByRole('searchbox', { name: 'Search' });
  await search.fill(slug);
  // After filtering, the matching card is still shown.
  await expect(page.locator(`a[href="/artifact/skill/${slug}"]`)).toBeVisible();

  // A search string that matches nothing collapses to the empty/zero state.
  await search.fill('zzz-no-such-artifact-zzz');
  await expect(cards).toHaveCount(0, { timeout: 5_000 });

  // Clear and open the first detail page.
  await search.fill('');
  await expect(cards.first()).toBeVisible();
  await page.locator('a[href^="/artifact/skill/"]').first().click();

  // Detail page: slug heading + rendered markdown body + frontmatter rail + eval.
  await expect(page).toHaveURL(/\/artifact\/skill\//);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  await expect(page.locator('article')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Frontmatter' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Evaluation' })).toBeVisible();
});
