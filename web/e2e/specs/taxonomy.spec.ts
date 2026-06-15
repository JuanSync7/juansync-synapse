// FR3.2 — Taxonomy view + edit + save. Runs against the TEMP-COPY sandbox so
// the save mutates a throwaway file, never the real taxonomy.
import { expect, test } from '@playwright/test';

test('views a taxonomy file and saves a non-breaking edit', async ({ page }) => {
  await page.goto('/taxonomy');
  await expect(page.getByRole('heading', { name: 'Taxonomy', level: 1 })).toBeVisible();

  // The first file is auto-selected; its rendered markdown shows in read mode.
  const fileButtons = page.locator('nav[aria-label="Taxonomy files"] button');
  await expect(fileButtons.first()).toBeVisible({ timeout: 15_000 });

  // Enter edit mode, append a harmless trailing line, save.
  await page.getByRole('button', { name: 'Edit' }).click();
  const editor = page.getByRole('textbox', { name: 'Edit taxonomy markdown' });
  await expect(editor).toBeVisible();
  const current = (await editor.inputValue()).replace(/\s+$/, '');
  await editor.fill(`${current}\n\n<!-- e2e taxonomy edit -->\n`);

  await expect(page.getByText('● unsaved')).toBeVisible();
  await page.getByRole('button', { name: 'Save' }).click();

  // Save succeeds → back to read mode (Edit button returns), no error surfaced.
  await expect(page.getByRole('button', { name: 'Edit' })).toBeVisible({ timeout: 10_000 });
});
