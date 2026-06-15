// Integration tests for the memo routes (FR5). GET runs against the REAL repo
// checkout (read-only — never mutates). The PATCH test runs against a TEMP
// FIXTURE repo so it never touches the real .brainstorms/ or change_requests/.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest';
import request from 'supertest';
import { createApp } from '../src/app';
import { resolveRepoRoot } from '../src/repo';
import { invalidateCache } from '../src/lib/crawler';

const realRoot = resolveRepoRoot();
const realApp = createApp(realRoot);

afterEach(() => invalidateCache());

describe('GET /api/memos (real repo, read-only)', () => {
  it('returns memos with counts, including one from the 2026-05-31 brainstorm session', async () => {
    const res = await request(realApp).get('/api/memos');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.memos)).toBe(true);
    expect(res.body.memos.length).toBeGreaterThan(0);
    expect(res.body.counts.total).toBe(res.body.memos.length);
    expect(res.body.counts.executed + res.body.counts.pending).toBe(res.body.counts.total);

    const fromSession = res.body.memos.filter(
      (m: { source: string }) => m.source === 'brainstorm:2026-05-31-vertical-slice-planning-stack',
    );
    expect(fromSession.length).toBeGreaterThanOrEqual(1);
  });

  it('filters by executed=false', async () => {
    const res = await request(realApp).get('/api/memos?executed=false');
    expect(res.status).toBe(200);
    expect(res.body.memos.every((m: { executed: boolean }) => m.executed === false)).toBe(true);
  });

  it('GET /:id returns the raw body for a known memo', async () => {
    const list = await request(realApp).get('/api/memos');
    const withFile = list.body.memos.find((m: { path: string | null }) => m.path !== null);
    expect(withFile).toBeDefined();
    const res = await request(realApp).get(`/api/memos/${withFile.id}`);
    expect(res.status).toBe(200);
    expect(typeof res.body.body).toBe('string');
    expect(res.body.body.length).toBeGreaterThan(0);
    expect(res.body.memo.id).toBe(withFile.id);
  });

  it('404s an unknown id', async () => {
    const res = await request(realApp).get('/api/memos/no__such__memo');
    expect(res.status).toBe(404);
  });
});

describe('PATCH /api/memos/:id (temp fixture only)', () => {
  let fixtureRoot: string;
  let app: ReturnType<typeof createApp>;

  beforeAll(() => {
    fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'synapse-memo-patch-'));
    const cr = path.join(fixtureRoot, 'src/protocols/foo/change_requests/2026-06-10-toggle.md');
    fs.mkdirSync(path.dirname(cr), { recursive: true });
    fs.writeFileSync(cr, '# Change Request — toggle me\n\nbody\n', 'utf8');
    app = createApp(fixtureRoot);
  });

  afterAll(() => {
    fs.rmSync(fixtureRoot, { recursive: true, force: true });
  });

  it('toggles executed and persists to the fixture, then 404s an unknown id', async () => {
    const list = await request(app).get('/api/memos');
    const memo = list.body.memos[0];
    expect(memo).toBeDefined();
    expect(memo.executed).toBe(false);

    const patch = await request(app).patch(`/api/memos/${memo.id}`).send({ executed: true });
    expect(patch.status).toBe(200);
    expect(patch.body.memo.executed).toBe(true);

    const onDisk = fs.readFileSync(
      path.join(fixtureRoot, 'src/protocols/foo/change_requests/2026-06-10-toggle.md'),
      'utf8',
    );
    expect(onDisk.startsWith('---\nexecuted: true\n---\n')).toBe(true);
    expect(onDisk).toContain('# Change Request — toggle me');

    const unknown = await request(app).patch('/api/memos/no__such').send({ executed: true });
    expect(unknown.status).toBe(404);
  });

  it('rejects a non-boolean executed with 400', async () => {
    const list = await request(app).get('/api/memos');
    const memo = list.body.memos[0];
    const res = await request(app).patch(`/api/memos/${memo.id}`).send({ executed: 'yes' });
    expect(res.status).toBe(400);
  });
});
