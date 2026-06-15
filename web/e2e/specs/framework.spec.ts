// FR4 — Framework page: creation lifecycle + base artifacts + pipeline presets.
import { expect, test } from '@playwright/test';

test('shows the lifecycle, base artifacts, and pipeline presets', async ({ page }) => {
  await page.goto('/framework');

  await expect(page.getByRole('heading', { name: 'Framework', level: 1 })).toBeVisible();

  // Creation lifecycle: the six ordered steps each carry a lifecycle-* testid.
  await expect(page.getByRole('heading', { name: 'creation lifecycle' })).toBeVisible();
  await expect(page.getByTestId('lifecycle-brainstormer')).toBeVisible({ timeout: 15_000 });
  const lifecycleSteps = page.locator('[data-testid^="lifecycle-"]');
  expect(await lifecycleSteps.count()).toBeGreaterThanOrEqual(5);

  // Base artifacts section + at least one synapse-layer artifact link.
  await expect(page.getByRole('heading', { name: 'Base artifacts' })).toBeVisible();
  await expect(page.locator('a[href^="/artifact/"]').first()).toBeVisible();

  // Pipeline presets (full / feature / bugfix) render as preset chips.
  await expect(page.getByRole('heading', { name: 'Pipeline' })).toBeVisible();
  await expect(page.getByTestId('preset-full')).toBeVisible();
  await expect(page.getByTestId('preset-feature')).toBeVisible();
  await expect(page.getByTestId('preset-bugfix')).toBeVisible();
});
