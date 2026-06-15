// Unit tests for the memo crawl + byte-preserving executed-flag PATCH (FR5).
// crawlMemos runs against a TEMP FIXTURE repo (a fake .brainstorms/<slug>/
// meta.yaml + a change_requests/foo.md + a frontmatter'd memo) so the three
// executed-resolution cases are asserted in isolation. setMemoExecuted writes
// only to the fixture — never the real working tree.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { crawlMemos, setMemoExecuted } from '../src/lib/memos';

let root: string;

/** Build a fixture repo exercising all three executed-resolution cases. */
function buildFixture(): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'synapse-memos-'));

  // (1) brainstorm session whose meta.yaml has a 'done' artifact (→ meta true)
  //     and a 'memo-placed' artifact (→ meta false); both join to memo files.
  const bdir = path.join(dir, '.brainstorms', '2026-05-31-vertical-slice-planning-stack');
  fs.mkdirSync(bdir, { recursive: true });
  fs.writeFileSync(
    path.join(bdir, 'meta.yaml'),
    [
      'slug: 2026-05-31-vertical-slice-planning-stack',
      'status: done',
      'artifacts_discovered: 2',
      'artifacts:',
      '  - name: delivery-plan-writer',
      '    type: skill',
      '    status: done',
      '    memo_type: new-artifact',
      '    memo_path: src/skills/delivery/change_requests/2026-06-10-plan-writer.md',
      '  - name: delivery-coding-contract',
      '    type: protocol',
      '    status: memo-placed',
      '    memo_type: new-artifact',
      '    memo_path: src/protocols/delivery/change_requests/2026-06-10-coding-contract.md',
      '',
    ].join('\n'),
    'utf8',
  );

  // The two brainstorm memo files (no frontmatter — body only).
  const m1 = path.join(dir, 'src/skills/delivery/change_requests/2026-06-10-plan-writer.md');
  fs.mkdirSync(path.dirname(m1), { recursive: true });
  fs.writeFileSync(m1, '# Decision Memo — delivery-plan-writer\n\n> Artifact type: skill\n\nbody\n', 'utf8');

  const m2 = path.join(dir, 'src/protocols/delivery/change_requests/2026-06-10-coding-contract.md');
  fs.mkdirSync(path.dirname(m2), { recursive: true });
  fs.writeFileSync(m2, '# Decision Memo — coding-contract\n\nbody\n', 'utf8');

  // (2) a standalone change_requests memo WITH frontmatter executed: true.
  const m3 = path.join(dir, 'src/agents/foo/change_requests/2026-05-13-standalone.md');
  fs.mkdirSync(path.dirname(m3), { recursive: true });
  fs.writeFileSync(
    m3,
    '---\nexecuted: true\ntitle: standalone\n---\n# Change Request — standalone\n\nbody here\n',
    'utf8',
  );

  // (3) a standalone change_requests memo with NO frontmatter and NO meta entry
  //     → default false.
  const m4 = path.join(dir, 'src/tools/bar/change_requests/2026-01-02-default.md');
  fs.mkdirSync(path.dirname(m4), { recursive: true });
  fs.writeFileSync(m4, '# Change Request — default memo\n\nbody\n', 'utf8');

  // A README inside a change_requests dir must be ignored, not treated as a memo.
  fs.writeFileSync(path.join(path.dirname(m4), 'README.md'), '# index\n', 'utf8');

  return dir;
}

beforeEach(() => {
  root = buildFixture();
});

afterEach(() => {
  fs.rmSync(root, { recursive: true, force: true });
});

describe('crawlMemos — executed resolution', () => {
  it('resolves all three cases (frontmatter true, meta done → true, default false)', () => {
    const memos = crawlMemos(root);

    const fm = memos.find((m) => m.path?.endsWith('2026-05-13-standalone.md'));
    expect(fm).toBeDefined();
    expect(fm?.executed).toBe(true);
    expect(fm?.executedSource).toBe('frontmatter');

    const metaDone = memos.find((m) => m.path?.endsWith('2026-06-10-plan-writer.md'));
    expect(metaDone?.executed).toBe(true);
    expect(metaDone?.executedSource).toBe('meta');
    expect(metaDone?.artifactType).toBe('skill');
    expect(metaDone?.session).toBe('2026-05-31-vertical-slice-planning-stack');

    const metaOpen = memos.find((m) => m.path?.endsWith('2026-06-10-coding-contract.md'));
    expect(metaOpen?.executed).toBe(false);
    expect(metaOpen?.executedSource).toBe('meta');

    const def = memos.find((m) => m.path?.endsWith('2026-01-02-default.md'));
    expect(def?.executed).toBe(false);
    expect(def?.executedSource).toBe('default');
  });

  it('ignores README.md inside change_requests dirs', () => {
    const memos = crawlMemos(root);
    expect(memos.some((m) => m.path?.endsWith('README.md'))).toBe(false);
  });

  it('derives a stable url-safe id and a created date from the filename', () => {
    const memos = crawlMemos(root);
    const def = memos.find((m) => m.path?.endsWith('2026-01-02-default.md'));
    expect(def?.id).toBe('src__tools__bar__change_requests__2026-01-02-default');
    expect(def?.createdDate).toBe('2026-01-02');
  });

  it('uses the first heading as the title', () => {
    const memos = crawlMemos(root);
    const def = memos.find((m) => m.path?.endsWith('2026-01-02-default.md'));
    expect(def?.title).toBe('Change Request — default memo');
  });

  it('tags standalone CRs with a change_requests source and brainstorm memos with a session source', () => {
    const memos = crawlMemos(root);
    const standalone = memos.find((m) => m.path?.endsWith('2026-05-13-standalone.md'));
    expect(standalone?.source.startsWith('change_requests:')).toBe(true);
    expect(standalone?.session).toBeNull();

    const fromSession = memos.find((m) => m.path?.endsWith('2026-06-10-plan-writer.md'));
    expect(fromSession?.source).toBe('brainstorm:2026-05-31-vertical-slice-planning-stack');
  });
});

describe('setMemoExecuted — byte-preserving frontmatter write', () => {
  it('updates the field in-place when frontmatter exists, body unchanged byte-for-byte', () => {
    const before = crawlMemos(root);
    const fm = before.find((m) => m.path?.endsWith('2026-05-13-standalone.md'));
    const absPath = path.join(root, fm!.path!);
    const original = fs.readFileSync(absPath, 'utf8');
    const bodyAfterFm = original.slice(original.indexOf('# Change Request'));

    const updated = setMemoExecuted(root, fm!.id, false);
    expect(updated.executed).toBe(false);
    expect(updated.executedSource).toBe('frontmatter');

    const after = fs.readFileSync(absPath, 'utf8');
    expect(after).toContain('executed: false');
    expect(after).not.toContain('executed: true');
    // Body after the frontmatter block is preserved byte-for-byte.
    expect(after.slice(after.indexOf('# Change Request'))).toBe(bodyAfterFm);
    // The other frontmatter field survives.
    expect(after).toContain('title: standalone');
  });

  it('prepends a frontmatter block when the file has none, original content preserved exactly', () => {
    const before = crawlMemos(root);
    const def = before.find((m) => m.path?.endsWith('2026-01-02-default.md'));
    const absPath = path.join(root, def!.path!);
    const original = fs.readFileSync(absPath, 'utf8');

    const updated = setMemoExecuted(root, def!.id, true);
    expect(updated.executed).toBe(true);
    expect(updated.executedSource).toBe('frontmatter');

    const after = fs.readFileSync(absPath, 'utf8');
    expect(after.startsWith('---\nexecuted: true\n---\n')).toBe(true);
    // The entire original body follows the prepended block, byte-for-byte.
    expect(after.slice('---\nexecuted: true\n---\n'.length)).toBe(original);
  });

  it('toggles back to false after being set true', () => {
    const before = crawlMemos(root);
    const def = before.find((m) => m.path?.endsWith('2026-01-02-default.md'));
    setMemoExecuted(root, def!.id, true);
    const mid = crawlMemos(root).find((m) => m.path?.endsWith('2026-01-02-default.md'));
    expect(mid?.executed).toBe(true);
    expect(mid?.executedSource).toBe('frontmatter');

    const updated = setMemoExecuted(root, def!.id, false);
    expect(updated.executed).toBe(false);
    const after = fs.readFileSync(path.join(root, def!.path!), 'utf8');
    expect(after).toContain('executed: false');
  });

  it('throws on an unknown id', () => {
    expect(() => setMemoExecuted(root, 'no__such__memo', true)).toThrow();
  });
});
