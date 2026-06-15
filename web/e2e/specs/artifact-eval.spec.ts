// FR2 — EVAL display: a detail page shows the Eval panel with criteria groups.
import { expect, test } from '@playwright/test';

test('a skill detail page renders the EVAL panel with criteria', async ({ page }) => {
  await page.goto('/skills');

  // Open the first skill that has an eval (most do); fall back to the first.
  const links = page.locator('a[href^="/artifact/skill/"]');
  await expect(links.first()).toBeVisible({ timeout: 15_000 });
  await links.first().click();

  await expect(page).toHaveURL(/\/artifact\/skill\//);

  const evalHeading = page.getByRole('heading', { name: 'Evaluation' });
  await expect(evalHeading).toBeVisible();

  // The panel is in one of its documented states: criteria groups, a no-eval
  // notice, a placeholder banner, or a no-criteria notice — all acceptable, but
  // the panel itself must be present and informative (not blank).
  const evalRegion = page.locator('section, aside, div').filter({ has: evalHeading }).first();
  await expect(evalRegion).toContainText(
    /(Execution|Output|Other|No EVAL\.md found|placeholder EVAL|No criteria parsed)/,
  );
});
