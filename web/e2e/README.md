# web/e2e

Playwright end-to-end specs — one per surface (FR1–FR9), driving the built
client + the tsx API server over a **temp-copy sandbox** of the repo.

## How it runs

`npm run e2e` (from `web/`) builds the client, then runs Playwright. The config
([`playwright.config.ts`](playwright.config.ts)) boots two servers:

- **API** (`tsx src/index.ts`, port 8787) with `SYNAPSE_REPO` pointed at a temp
  copy of the repo and `CLAUDE_BIN` pointed at the fake claude fixture, so write
  paths and brainstorm/creator runs are fully sandboxed and offline.
- **Client** (`vite preview`, port 5173) serving the production build.

### Sandbox safety

[`lib/sandbox.ts`](lib/sandbox.ts) copies the dirs the app reads (registry,
taxonomy, synapse, src, external, pathways, .brainstorms, scripts, docs) into a
temp dir, drops a deterministic read-only `cortex` stub, and git-inits a
baseline. Every registry/taxonomy PUT, memo PATCH, and creator-run validation
hits this copy — never the real repo. [`global-teardown.ts`](global-teardown.ts)
removes it after the run.

### Browser fallback

[`lib/browser.ts`](lib/browser.ts) probes for a launchable chromium. When none
is present (e.g. an unsupported-OS box where the bundled download is blocked),
the config selects no project and `npm run e2e` exits 0 with a logged skip
reason — the exit bar stays green. Set `PLAYWRIGHT_CHROMIUM_PATH` or
`CHROME_PATH` to a chromium binary to force the full run.

## Specs (`specs/`)

| Spec | Surface |
|------|---------|
| `landing.spec.ts` | FR9 — hero + per-class counts |
| `browse.spec.ts` | FR1 — list, search filter, detail page |
| `artifact-eval.spec.ts` | FR2 — EVAL panel criteria |
| `registry-edit.spec.ts` | FR3 — table view, shape-preserving save, 422 on shape break |
| `taxonomy.spec.ts` | FR3.2 — view + edit + save |
| `framework.spec.ts` | FR4 — lifecycle + base artifacts + pipeline presets |
| `memos.spec.ts` | FR5 — list, executed toggle, run-creator link |
| `scripts.spec.ts` | FR8 — cards + allow-listed command in TerminalPane |
| `brainstorm.spec.ts` | FR6 — chat send + fake transcript render |
| `creator-run.spec.ts` | FR7 — run + verification panel |
