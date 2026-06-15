// FR6 — Headless brainstorm chat. With CLAUDE_BIN=fake (set on the e2e API
// server), sending a first message spawns the fake claude, whose canned
// transcript (assistant text + a result line) renders in the ChatStream.
import { expect, test } from '@playwright/test';

test('sends a first message and renders the fake assistant transcript', async ({ page }) => {
  await page.goto('/brainstorm');
  await expect(page.getByRole('heading', { name: 'Brainstorm', level: 1 })).toBeVisible();

  // Type a first message and send.
  const input = page.getByRole('textbox', { name: 'Message' });
  await input.fill('Explore a skill for summarising changelogs.');
  await page.getByRole('button', { name: 'Send' }).click();

  // The ChatStream renders the fake's canned assistant text and the result line.
  const stream = page.getByTestId('chat-stream');
  await expect(stream).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId('assistant-text').first()).toContainText('Hello from fake claude.', {
    timeout: 20_000,
  });
  await expect(page.getByTestId('result-marker')).toContainText('Done from fake claude.', {
    timeout: 20_000,
  });

  // The session reaches a terminal status (done).
  await expect(page.getByTestId('session-status')).toContainText(/done|running/, { timeout: 20_000 });
});
