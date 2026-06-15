// System smoke (task step 4 / NFR3): boot the full app against the REAL repo
// checkout and assert every GET endpoint returns 200 with sane data. This is the
// integration sanity net the e2e suite leans on — if a route module fails to
// wire up or a crawl throws, this fails loudly and fast (no browser needed). It
// is strictly READ-ONLY: it hits no PUT/PATCH/POST and never spawns claude.
import { afterEach, describe, expect, it } from 'vitest';
import request from 'supertest';
import { createApp } from '../src/app';
import { resolveRepoRoot } from '../src/repo';
import { invalidateCache } from '../src/lib/crawler';

const app = createApp(resolveRepoRoot());

afterEach(() => invalidateCache());

describe('GET smoke — every read endpoint returns 200 with sane data', () => {
  it('GET /api/health', async () => {
    const res = await request(app).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.body.ok).toBe(true);
    expect(typeof res.body.repoRoot).toBe('string');
  });

  for (const cls of ['skill', 'agent', 'protocol', 'tool', 'pathway'] as const) {
    it(`GET /api/artifacts?class=${cls}`, async () => {
      const res = await request(app).get(`/api/artifacts?class=${cls}`);
      expect(res.status).toBe(200);
      expect(Array.isArray(res.body.items)).toBe(true);
      expect(res.body.counts).toBeTruthy();
      expect(typeof res.body.counts[cls]).toBe('number');
    });
  }

  it('GET /api/pipeline', async () => {
    const res = await request(app).get('/api/pipeline');
    expect(res.status).toBe(200);
    // The parsed SKILLS_REGISTRY.yaml carries stages and/or presets.
    expect(res.body).toBeTruthy();
    expect(typeof res.body).toBe('object');
  });

  it('GET /api/registry (list)', async () => {
    const res = await request(app).get('/api/registry');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.files)).toBe(true);
    expect(res.body.files.length).toBeGreaterThan(0);
  });

  it('GET /api/taxonomy (list)', async () => {
    const res = await request(app).get('/api/taxonomy');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.files)).toBe(true);
    expect(res.body.files.length).toBeGreaterThan(0);
  });

  it('GET /api/framework', async () => {
    const res = await request(app).get('/api/framework');
    expect(res.status).toBe(200);
    expect(res.body).toBeTruthy();
  });

  it('GET /api/scripts', async () => {
    const res = await request(app).get('/api/scripts');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.scripts)).toBe(true);
    expect(res.body.scripts.length).toBeGreaterThan(0);
  });

  it('GET /api/memos', async () => {
    const res = await request(app).get('/api/memos');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.memos)).toBe(true);
  });

  it('GET /api/sessions (list)', async () => {
    const res = await request(app).get('/api/sessions');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.sessions)).toBe(true);
  });

  it('GET /api/runs (list)', async () => {
    const res = await request(app).get('/api/runs');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.runs)).toBe(true);
  });
});
