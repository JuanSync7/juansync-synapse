// FR3 — Registry editing. Runs against the TEMP-COPY sandbox repo (see
// playwright.config.ts), so every save mutates throwaway files, never the real
// registry. Asserts: table view, a shape-PRESERVING edit saves successfully, and
// a shape-BREAKING edit (a dropped column) surfaces the server's 422.
import { expect, test } from '@playwright/test';

/** Drop the last column from a GFM table's header + separator rows. */
function dropLastColumn(raw: string): string {
  const lines = raw.split('\n');
  let headerIdx = -1;
  for (let i = 0; i < lines.length - 1; i++) {
    const h = lines[i] ?? '';
    const sep = lines[i + 1] ?? '';
    if (h.includes('|') && /^\s*\|?[\s:|-]+\|?\s*$/.test(sep) && sep.includes('-')) {
      headerIdx = i;
      break;
    }
  }
  if (headerIdx === -1) return raw + '\n| extra |\n'; // fallback shape break
  const chop = (row: string): string => {
    const cells = row.split('|');
    // Drop the last non-empty cell to change the column count.
    if (cells.length <= 2) return row;
    cells.splice(cells.length - 2, 1);
    return cells.join('|');
  };
  lines[headerIdx] = chop(lines[headerIdx] as string);
  lines[headerIdx + 1] = chop(lines[headerIdx + 1] as string);
  return lines.join('\n');
}

test('renders a registry table and saves a shape-preserving edit', async ({ page }) => {
  await page.goto('/registry');
  await expect(page.getByRole('heading', { name: 'Registry', level: 1 })).toBeVisible();

  // Pick the skills registry — a known clean table.
  await page.getByRole('button', { name: 'SKILL_REGISTRY', exact: false }).first().click();
  await expect(page.locator('table')).toBeVisible({ timeout: 15_000 });
  await expect(page.locator('table thead th').first()).toBeVisible();

  // Enter edit mode and make a shape-preserving edit (append a trailing comment
  // — the table columns are untouched, so the same-shape guard passes).
  await page.getByRole('button', { name: 'Edit' }).click();
  const editor = page.getByRole('textbox', { name: 'Edit registry markdown' });
  await expect(editor).toBeVisible();
  const current = (await editor.inputValue()).replace(/\s+$/, '');
  await editor.fill(`${current}\n\n<!-- e2e shape-preserving edit -->\n`);

  // Dirty indicator appears; Save succeeds and returns to table view.
  await expect(page.getByText('● unsaved')).toBeVisible();
  await page.getByRole('button', { name: 'Save' }).click();
  await expect(page.getByRole('button', { name: 'Edit' })).toBeVisible({ timeout: 10_000 });
  // No error surfaced.
  await expect(page.getByText(/Edit rejected/)).toHaveCount(0);
});

test('a shape-breaking edit surfaces the 422 error', async ({ page }) => {
  await page.goto('/registry');
  await page.getByRole('button', { name: 'SKILL_REGISTRY', exact: false }).first().click();
  await expect(page.locator('table')).toBeVisible({ timeout: 15_000 });

  await page.getByRole('button', { name: 'Edit' }).click();
  const editor = page.getByRole('textbox', { name: 'Edit registry markdown' });
  const broken = dropLastColumn(await editor.inputValue());
  await editor.fill(broken);
  await page.getByRole('button', { name: 'Save' }).click();

  // The server rejects with 422; the page surfaces the error text and stays in
  // edit mode (Save button still present).
  await expect(page.getByText(/Edit rejected|same columns/)).toBeVisible({ timeout: 10_000 });
  await expect(page.getByRole('button', { name: 'Save' })).toBeVisible();
});
