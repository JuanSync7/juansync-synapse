// FR8 — Scripts control panel: cards render, and running an allow-listed
// read-only command shows TerminalPane output. The command runs the `cortex`
// stub in the temp-copy sandbox (deterministic, exit 0) — never mutating.
import { expect, test } from '@playwright/test';

test('shows script cards and runs an allow-listed read-only command', async ({ page }) => {
  await page.goto('/scripts');
  await expect(page.getByRole('heading', { name: 'Scripts', level: 1 })).toBeVisible();

  // Card grid is populated.
  await expect(page.locator('ul li').first()).toBeVisible({ timeout: 15_000 });

  // Run an allow-listed read-only command (cortex list). The sandbox cortex stub
  // answers it with exit 0.
  const runBtn = page.getByRole('button', { name: 'Run cortex list' });
  await expect(runBtn).toBeVisible();
  await runBtn.click();

  // TerminalPane renders with the command line and an exit badge (exit 0).
  const pane = page.getByTestId('terminal-pane');
  await expect(pane).toBeVisible({ timeout: 15_000 });
  await expect(pane).toContainText('$ ./cortex list');
  await expect(page.getByTestId('exit-badge')).toHaveText(/exit 0/);
});
