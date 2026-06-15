// FR9 — Landing: hero + live per-class counts.
import { expect, test } from '@playwright/test';

test('shows the Synapse hero and per-class counts', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('heading', { name: 'Synapse', level: 1 })).toBeVisible();

  // Each artifact class has a count numeral that resolves to a number (not the
  // unloaded em-dash) once the crawler responds.
  for (const cls of ['skill', 'agent', 'protocol', 'tool', 'pathway']) {
    const count = page.getByTestId(`count-${cls}`);
    await expect(count).toBeVisible();
    await expect(count).toHaveText(/^\d+$/, { timeout: 15_000 });
  }

  // Framework + repo links are present.
  await expect(page.getByRole('link', { name: /Framework & pipeline/ })).toBeVisible();
  await expect(page.getByRole('link', { name: 'GitHub repo →' })).toBeVisible();
});
