// FR7 — Creator end-to-end run. Picks a real memo id from the API, starts a run
// with CLAUDE_BIN=fake against the temp-copy sandbox (its `cortex` stub makes
// validate exit 0), and asserts the verification panel appears. The fake claude
// + sandbox cortex stub mean no real claude and no real validate ever run.
import { expect, test } from '@playwright/test';

test('runs the creator against a memo and shows the verification panel', async ({ page, request }) => {
  // Pick a real memo id from the API (proxied through the client origin).
  const res = await request.get('/api/memos');
  expect(res.ok()).toBeTruthy();
  const body = (await res.json()) as { memos: Array<{ id: string; path?: string }> };
  const memo = body.memos.find((m) => m.path);
  expect(memo, 'expected at least one memo with a file path in the sandbox').toBeTruthy();
  const memoId = (memo as { id: string }).id;

  await page.goto(`/runs?memo=${encodeURIComponent(memoId)}`);
  await expect(page.getByRole('heading', { name: 'Creator Run', level: 1 })).toBeVisible();

  // The preselected memo is reflected; start the run.
  await expect(page.getByTestId('target-memo')).toBeVisible();
  await page.getByRole('button', { name: 'Run creator' }).click();

  // Navigates to /runs/:id and streams the fake transcript.
  await expect(page).toHaveURL(/\/runs\/[0-9a-f-]+/, { timeout: 20_000 });
  await expect(page.getByTestId('chat-stream')).toBeVisible({ timeout: 20_000 });

  // The verification panel appears once the run completes (git diff + validate).
  await expect(page.getByTestId('verification-panel')).toBeVisible({ timeout: 30_000 });
  await expect(page.getByRole('heading', { name: 'validation' })).toBeVisible();
  // Run banner reflects a terminal verdict.
  await expect(page.getByTestId('run-banner')).toContainText(/run (succeeded|failed)/, {
    timeout: 30_000,
  });
});
