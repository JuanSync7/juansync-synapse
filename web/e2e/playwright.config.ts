import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig } from '@playwright/test';
import { buildSandbox } from './lib/sandbox';
import { hasChromium, resolveChromium } from './lib/browser';

// --- repo + sandbox wiring (task step 2) -----------------------------------
//
// The real repo root is web/'s parent. We build a TEMP COPY sandbox here, at
// config-eval time (before the webServer boots), so the API server can point
// SYNAPSE_REPO at it — every write-path spec (registry/taxonomy PUT, memo
// PATCH, creator-run) is then confined to throwaway files. The sandbox path is
// exported via env so the webServer subprocess and specs both see the same one.
// Teardown happens in global-teardown.ts.
const here = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(here, '..');
const realRepo = path.resolve(webRoot, '..');
const fakeClaude = path.join(webRoot, 'server', 'test', 'fixtures', 'fake-claude.mjs');

const browserAvailable = hasChromium();

// Build the sandbox only when we will actually run a browser — no point copying
// the repo if every spec is going to skip.
let sandboxRepo = '';
if (browserAvailable) {
  sandboxRepo = buildSandbox(realRepo).repoRoot;
  // Stash the path so global-teardown can remove it after the run.
  process.env.SYNAPSE_E2E_SANDBOX = sandboxRepo;
} else {
  console.warn(
    '\n[e2e] No launchable chromium found for this platform — skipping all e2e ' +
      'specs (reported as skipped, not failed). Playwright 1.60 does not support ' +
      "this OS's bundled download and no system chrome is present. Set " +
      'PLAYWRIGHT_CHROMIUM_PATH or CHROME_PATH to a chromium binary to run them.\n',
  );
}

const PORT_API = 8787;
const PORT_CLIENT = 5173;

export default defineConfig({
  testDir: './specs',
  // No specs run when there's no browser — but the runner still exits 0 because
  // the projects array is empty (combined with --pass-with-no-tests in the npm
  // script). When a browser exists, the single chromium project runs everything.
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [['list']],
  globalTeardown: browserAvailable ? './global-teardown.ts' : undefined,
  use: {
    baseURL: `http://localhost:${PORT_CLIENT}`,
    trace: 'retain-on-failure',
  },
  // Empty project list ⇒ no tests selected ⇒ clean exit when chromium is absent.
  projects: browserAvailable
    ? [
        {
          name: 'chromium',
          use: {
            // Drive the explicitly resolved executable (env override or a
            // distro-agnostic Chrome-for-Testing build), since Playwright has no
            // bundled chromium for this OS. --no-sandbox is required as we run as
            // an unprivileged user with no user namespaces; the rest are headless
            // stability flags for CI-shaped containers.
            launchOptions: {
              executablePath: resolveChromium() ?? undefined,
              args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
            },
          },
        },
      ]
    : [],
  // Only boot servers when we will actually run specs.
  webServer: browserAvailable
    ? [
        {
          // PREFERRED fix for the dist-ESM issue (task): run the server under tsx,
          // exactly like dev — no build needed, imports resolve at runtime.
          command: 'npm run dev --workspace server',
          cwd: webRoot,
          port: PORT_API,
          reuseExistingServer: false,
          timeout: 60_000,
          env: {
            PORT: String(PORT_API),
            // SAFETY: server reads + WRITES go to the temp-copy sandbox only.
            SYNAPSE_REPO: sandboxRepo,
            // SAFETY: brainstorm/creator never spawn the real claude binary.
            CLAUDE_BIN: fakeClaude,
          },
        },
        {
          // Built client served by vite preview — stable, production-shaped.
          command: 'npm run preview --workspace client -- --port ' + PORT_CLIENT + ' --strictPort',
          cwd: webRoot,
          port: PORT_CLIENT,
          reuseExistingServer: false,
          timeout: 120_000,
        },
      ]
    : undefined,
});
