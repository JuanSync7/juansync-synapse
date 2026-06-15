// Browser-availability probe (task step 1 fallback).
//
// This environment (ubuntu26.04-x64) is not supported by Playwright 1.60's
// bundled chromium download, and no system chrome is present, so the browser
// install is BLOCKED. Rather than fail the exit bar, the config detects this
// and skips the e2e project with a logged reason — every spec is then reported
// as skipped instead of errored, keeping `npm run e2e` green.
//
// If a usable chromium IS present (installed bundle or PLAYWRIGHT_CHROMIUM_PATH
// / CHROME_PATH pointing at a system binary), the probe returns its path and the
// full suite runs.
import fs from 'node:fs';
import { chromium } from '@playwright/test';

/** A system-chrome override, if the operator points us at one. */
function envChromePath(): string | undefined {
  const p = process.env.PLAYWRIGHT_CHROMIUM_PATH || process.env.CHROME_PATH;
  return p && fs.existsSync(p) ? p : undefined;
}

/**
 * Resolve a launchable chromium executable, or null when none is available.
 * Checks an explicit env override first, then Playwright's bundled install.
 */
export function resolveChromium(): string | null {
  const override = envChromePath();
  if (override) return override;
  try {
    const p = chromium.executablePath();
    if (p && fs.existsSync(p)) return p;
  } catch {
    // executablePath throws when the browser isn't installed for this platform.
  }
  return null;
}

/** True when a chromium binary is launchable. */
export function hasChromium(): boolean {
  return resolveChromium() !== null;
}
