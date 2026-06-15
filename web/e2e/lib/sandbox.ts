// e2e sandbox builder (SAFETY / task step 2).
//
// The e2e API server must never mutate the real repo. Registry/taxonomy/memo
// write-path specs go through PUT/PATCH, and a creator run shells out to
// `./cortex validate`. So we point the server's SYNAPSE_REPO at a TEMP COPY of
// the repo built here, and drop in a deterministic `cortex` stub that answers
// the read-only allow-listed subcommands (validate/list/available/doctor/
// pin status/pathway list) with exit 0 — no python, no network, fully offline.
//
// We copy the dirs the app actually reads. The copy is git-init'd + committed so
// the creator-run git-porcelain diff is run-scoped (a non-repo would yield an
// empty baseline, which still works, but a real repo exercises the diff path).
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

/** Directories the server reads, relative to the repo root. */
const COPY_DIRS = [
  'registry',
  'taxonomy',
  'synapse',
  'src',
  'external',
  'pathways',
  '.brainstorms',
  'scripts',
  'docs',
] as const;

/** A `cortex` stub: answers the FR8.3 read-only allow-list, exit 0. */
const CORTEX_STUB = `#!/usr/bin/env bash
# e2e cortex stub — deterministic, offline, read-only. Mirrors the real
# dispatcher's surface only for the allow-listed read-only subcommands so the
# scripts panel + creator-run verification have something to run safely.
set -euo pipefail
case "\${1:-}" in
  validate)  echo "Validating all artifacts..."; echo; echo "0 error(s), 0 warning(s)"; exit 0 ;;
  list)      echo "Installed synapses (sandbox):"; echo "  (none — e2e sandbox)"; exit 0 ;;
  available) echo "Available synapses (sandbox):"; echo "  skill   docs-spec-writer"; exit 0 ;;
  doctor)    echo "cortex doctor: OK (sandbox)"; exit 0 ;;
  pin)       echo "pin \${2:-}: clean (sandbox)"; exit 0 ;;
  pathway)   echo "pathways (sandbox): (none)"; exit 0 ;;
  *)         echo "cortex (e2e sandbox): unknown command '\${1:-}'" >&2; exit 2 ;;
esac
`;

export interface Sandbox {
  /** Absolute path to the temp repo copy (use as SYNAPSE_REPO). */
  repoRoot: string;
}

/** Recursively copy a directory if it exists (best effort, no symlinks). */
function copyDirIfPresent(src: string, dest: string): void {
  if (!fs.existsSync(src)) return;
  fs.cpSync(src, dest, { recursive: true, dereference: true });
}

/**
 * Build the temp-copy sandbox repo. Copies the read dirs, drops a cortex stub,
 * gitignores web/, and commits a baseline. Returns the temp repo root.
 */
export function buildSandbox(realRepo: string): Sandbox {
  const repoRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'synapse-e2e-'));

  for (const dir of COPY_DIRS) {
    copyDirIfPresent(path.join(realRepo, dir), path.join(repoRoot, dir));
  }

  // The cortex dispatcher stub (looksLikeRepoRoot + safeExec require it).
  const cortex = path.join(repoRoot, 'cortex');
  fs.writeFileSync(cortex, CORTEX_STUB, 'utf8');
  fs.chmodSync(cortex, 0o755);

  // web/ (the run/session store) must be ignored so the creator-run diff never
  // reports the sandbox's own .sessions files as "created paths".
  fs.writeFileSync(path.join(repoRoot, '.gitignore'), 'web/\nnode_modules/\n', 'utf8');

  // Commit a baseline so `git status --porcelain` only shows a run's own work.
  try {
    execFileSync('git', ['init', '-q'], { cwd: repoRoot });
    execFileSync('git', ['config', 'user.email', 'e2e@synapse.test'], { cwd: repoRoot });
    execFileSync('git', ['config', 'user.name', 'synapse-e2e'], { cwd: repoRoot });
    execFileSync('git', ['add', '-A'], { cwd: repoRoot });
    execFileSync('git', ['commit', '-q', '-m', 'e2e sandbox baseline'], { cwd: repoRoot });
  } catch {
    // git absent or commit failed — the run's diff baseline just falls back to
    // empty; the sandbox is still usable for read + write-path specs.
  }

  return { repoRoot };
}

/** Remove a sandbox repo (best effort). */
export function teardownSandbox(repoRoot: string): void {
  try {
    fs.rmSync(repoRoot, { recursive: true, force: true });
  } catch {
    /* best effort */
  }
}
