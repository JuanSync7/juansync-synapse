import fs from 'node:fs';
import path from 'node:path';
import { afterEach, describe, expect, it } from 'vitest';
import request from 'supertest';
import { createApp } from '../src/app';
import { resolveRepoRoot } from '../src/repo';

describe('resolveRepoRoot', () => {
  afterEach(() => {
    delete process.env.SYNAPSE_REPO;
  });

  it('walks upward from cwd and finds this repo (cortex file + synapse/ dir)', () => {
    const root = resolveRepoRoot();
    expect(fs.statSync(path.join(root, 'cortex')).isFile()).toBe(true);
    expect(fs.statSync(path.join(root, 'synapse')).isDirectory()).toBe(true);
  });

  it('prefers SYNAPSE_REPO env when set', () => {
    process.env.SYNAPSE_REPO = '/tmp/some-adopter-checkout';
    expect(resolveRepoRoot()).toBe('/tmp/some-adopter-checkout');
  });
});

describe('GET /api/health', () => {
  it('returns 200 with { ok: true, repoRoot }', async () => {
    const repoRoot = resolveRepoRoot();
    const app = createApp(repoRoot);
    const res = await request(app).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ ok: true, repoRoot });
  });
});
