// Unit tests for the creator-run driver (FR7). NEVER spawns real claude
// (CLAUDE_BIN → fake fixture) and NEVER runs the real `./cortex validate`: the
// repoRoot is a TEMP git repo with a `cortex` stub that exits 0 (success case)
// or 1 (failing-validate case). The fake claude actually CREATES a file in the
// repo so `git status --porcelain` shows a change, exercising the real git-diff
// verification path. All run meta lands under <temp>/web/.sessions/runs.
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
  getRun,
  inferArtifact,
  listRuns,
  readVerification,
  runsDir,
  startCreatorRun,
} from '../src/lib/creatorRun';
import { defaultSessionDir } from '../src/lib/claudeSession';

const here = path.dirname(fileURLToPath(import.meta.url));
const FAKE = path.join(here, 'fixtures', 'fake-claude.mjs');

let repoRoot: string;
let sessionDir: string;
const savedBin = process.env.CLAUDE_BIN;
const savedCreate = process.env.FAKE_CLAUDE_CREATE_FILE;

/** Make a temp git repo with a memo under change_requests/ and a cortex stub. */
function makeRepo(validateExit: 0 | 1): { memoId: string } {
  repoRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'synapse-run-'));
  execFileSync('git', ['init', '-q'], { cwd: repoRoot });
  execFileSync('git', ['config', 'user.email', 't@t.t'], { cwd: repoRoot });
  execFileSync('git', ['config', 'user.name', 'tester'], { cwd: repoRoot });

  // A memo under a change_requests/ dir so crawlMemos picks it up.
  const memoDir = path.join(repoRoot, 'src', 'skills', 'demo', 'change_requests');
  fs.mkdirSync(memoDir, { recursive: true });
  const memoRel = 'src/skills/demo/change_requests/2026-06-13-demo.md';
  fs.writeFileSync(path.join(repoRoot, memoRel), '# Demo memo\n\nspec body\n', 'utf8');

  // Mirror the real repo: web/.sessions is gitignored, so the run store never
  // shows up as a "created path" in the verification diff.
  fs.writeFileSync(path.join(repoRoot, '.gitignore'), 'web/\n', 'utf8');

  // A cortex stub the safeExec allow-list permits (`./cortex validate`).
  const cortex = path.join(repoRoot, 'cortex');
  fs.writeFileSync(
    cortex,
    validateExit === 0 ? '#!/usr/bin/env bash\necho "0 errors / 0 warnings"\nexit 0\n' : '#!/usr/bin/env bash\necho "1 error" >&2\nexit 1\n',
    'utf8',
  );
  fs.chmodSync(cortex, 0o755);

  // Commit the baseline so only the run's own changes show in porcelain.
  execFileSync('git', ['add', '-A'], { cwd: repoRoot });
  execFileSync('git', ['commit', '-q', '-m', 'baseline'], { cwd: repoRoot });

  sessionDir = defaultSessionDir(repoRoot);
  // memo id is path-derived: `/`→`__`, `.md` stripped.
  const memoId = memoRel.replace(/\.md$/, '').split('/').join('__');
  return { memoId };
}

/** Wait until the run reaches a terminal status (or time out). */
async function waitForTerminal(id: string, ms = 6000): Promise<string> {
  const deadline = Date.now() + ms;
  for (;;) {
    const meta = getRun(sessionDir, id);
    if (meta && meta.status !== 'running') return meta.status;
    if (Date.now() > deadline) throw new Error('run never reached terminal status');
    await new Promise((r) => setTimeout(r, 50));
  }
}

beforeEach(() => {
  process.env.CLAUDE_BIN = FAKE;
});

afterEach(() => {
  if (repoRoot) fs.rmSync(repoRoot, { recursive: true, force: true });
  if (savedBin === undefined) delete process.env.CLAUDE_BIN;
  else process.env.CLAUDE_BIN = savedBin;
  if (savedCreate === undefined) delete process.env.FAKE_CLAUDE_CREATE_FILE;
  else process.env.FAKE_CLAUDE_CREATE_FILE = savedCreate;
});

describe('inferArtifact', () => {
  it('maps a SKILL.md path to {class, slug}', () => {
    expect(inferArtifact('src/skills/foo/foo-bar/SKILL.md')).toEqual({
      class: 'skill',
      slug: 'foo-bar',
    });
    expect(inferArtifact('src/tools/x/my-tool/TOOL.md')).toEqual({ class: 'tool', slug: 'my-tool' });
    expect(inferArtifact('src/skills/foo/README.md')).toBeNull();
  });
});

describe('startCreatorRun (fake claude + temp git repo)', () => {
  it('resolves the memo, runs to completion, diffs git, validates, marks succeeded', async () => {
    const { memoId } = makeRepo(0);
    // The fake claude creates a new artifact file → shows up in git porcelain.
    const createdAbs = path.join(repoRoot, 'src', 'skills', 'demo', 'demo-skill', 'SKILL.md');
    process.env.FAKE_CLAUDE_CREATE_FILE = createdAbs;

    const run = await startCreatorRun({ repoRoot, memoId, sessionDir });
    expect(run.meta.memoPath).toBe('src/skills/demo/change_requests/2026-06-13-demo.md');
    expect(run.meta.status).toBe('running');

    const status = await waitForTerminal(run.id);
    expect(status).toBe('succeeded');

    const verification = readVerification(sessionDir, run.id);
    expect(verification).not.toBeNull();
    expect(verification!.validate.exitCode).toBe(0);
    const created = verification!.createdPaths.map((c) => c.path);
    expect(created).toContain('src/skills/demo/demo-skill/SKILL.md');
    // The new SKILL.md is recognized as an artifact with class+slug.
    const art = verification!.createdPaths.find(
      (c) => c.path === 'src/skills/demo/demo-skill/SKILL.md',
    );
    expect(art?.artifact).toEqual({ class: 'skill', slug: 'demo-skill' });

    // Listed and addressable.
    expect(listRuns(sessionDir).some((r) => r.id === run.id)).toBe(true);
    expect(getRun(sessionDir, run.id)?.status).toBe('succeeded');
  });

  it('marks failed when validate exits nonzero', async () => {
    const { memoId } = makeRepo(1);
    const run = await startCreatorRun({ repoRoot, memoId, sessionDir });
    const status = await waitForTerminal(run.id);
    expect(status).toBe('failed');
    expect(readVerification(sessionDir, run.id)?.validate.exitCode).toBe(1);
  });

  it('rejects with NOT_FOUND for an unknown memo id', async () => {
    makeRepo(0);
    await expect(
      startCreatorRun({ repoRoot, memoId: 'no-such-memo', sessionDir }),
    ).rejects.toMatchObject({ code: 'NOT_FOUND' });
  });

  it('stores run meta under <sessionDir>/runs', async () => {
    const { memoId } = makeRepo(0);
    const run = await startCreatorRun({ repoRoot, memoId, sessionDir });
    await waitForTerminal(run.id);
    const metaFile = path.join(runsDir(sessionDir), `${run.id}.meta.json`);
    expect(fs.existsSync(metaFile)).toBe(true);
    expect(metaFile.includes(path.join('web', '.sessions', 'runs'))).toBe(true);
  });
});
