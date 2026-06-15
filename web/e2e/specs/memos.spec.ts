// FR5 — Memos: list, executed toggle (against the temp-copy sandbox), and a
// "Run creator with this memo" link into /runs.
import { expect, test } from '@playwright/test';

test('lists memos, toggles executed, and links a memo to a creator run', async ({ page }) => {
  await page.goto('/memos');
  await expect(page.getByRole('heading', { name: 'Memos', level: 1 })).toBeVisible();

  // Filter buttons present.
  await expect(page.getByRole('button', { name: /^All/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /^Pending/ })).toBeVisible();

  // At least one memo row (sandbox copies the real .brainstorms + change_requests).
  // Only FILE-BACKED memos have an enabled toggle; brainstorm-only memos render a
  // disabled checkbox. Target the first ENABLED one so the toggle actually fires.
  const enabledToggle = page.getByRole('checkbox').and(page.locator(':enabled')).first();
  await expect(enabledToggle).toBeVisible({ timeout: 15_000 });

  // Toggle its executed flag and confirm the checkbox reflects it (the PATCH
  // lands in the temp-copy sandbox, never the real memo file).
  const before = await enabledToggle.isChecked();
  await enabledToggle.click();
  await expect(enabledToggle).toBeChecked({ checked: !before, timeout: 10_000 });

  // Open a memo drawer (any row's title button) and follow the "Run creator" link.
  const rowOpen = page.getByTestId('memo-open').first();
  await rowOpen.click();

  const runLink = page.getByRole('link', { name: 'Run creator with this memo' });
  await expect(runLink).toBeVisible({ timeout: 10_000 });
  await expect(runLink).toHaveAttribute('href', /\/runs\?memo=/);
  await runLink.click();
  await expect(page).toHaveURL(/\/runs\?memo=/);
  await expect(page.getByRole('heading', { name: 'Creator Run', level: 1 })).toBeVisible();
});
