// Integration tests for the registry + taxonomy editing routes. CRITICAL: these
// run against a TEMP FIXTURE repo (copied from a couple of real registry/taxonomy
// files), so PUT writes hit the fixture, never the real working tree.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest';
import request from 'supertest';
import { createApp } from '../src/app';
import { resolveRepoRoot } from '../src/repo';
import { invalidateCache } from '../src/lib/crawler';

let fixtureRoot: string;
let app: ReturnType<typeof createApp>;

beforeAll(() => {
  const realRoot = resolveRepoRoot();
  fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'synapse-fixture-'));
  // createApp's repoRoot is only used for the registry/taxonomy file paths here.
  fs.mkdirSync(path.join(fixtureRoot, 'registry'), { recursive: true });
  fs.mkdirSync(path.join(fixtureRoot, 'taxonomy'), { recursive: true });

  const copy = (rel: string) =>
    fs.copyFileSync(path.join(realRoot, rel), path.join(fixtureRoot, rel));

  copy('registry/SKILL_REGISTRY.md');
  copy('registry/SKILL_VOCABULARY.md');
  copy('taxonomy/SKILL_TAXONOMY.md');

  app = createApp(fixtureRoot);
});

afterEach(() => invalidateCache());

afterAll(() => {
  fs.rmSync(fixtureRoot, { recursive: true, force: true });
});

describe('GET /api/registry', () => {
  it('lists SKILL_REGISTRY and tags the vocabulary', async () => {
    const res = await request(app).get('/api/registry');
    expect(res.status).toBe(200);
    const names = res.body.files.map((f: { name: string }) => f.name);
    expect(names).toContain('SKILL_REGISTRY.md');
    const vocab = res.body.files.find((f: { name: string }) => f.name === 'SKILL_VOCABULARY.md');
    expect(vocab.kind).toBe('vocabulary');
  });
});

describe('GET /api/registry/:name', () => {
  it('returns a parsed table for SKILL_REGISTRY.md', async () => {
    const res = await request(app).get('/api/registry/SKILL_REGISTRY.md');
    expect(res.status).toBe(200);
    expect(res.body.raw).toContain('# Skills Registry');
    expect(res.body.table).not.toBeNull();
    expect(res.body.table.headers).toContain('Skill');
    expect(res.body.table.rows.length).toBeGreaterThan(0);
  });

  it('404s an unknown name', async () => {
    const res = await request(app).get('/api/registry/NOPE.md');
    expect(res.status).toBe(404);
  });
});

describe('PUT /api/registry/:name', () => {
  it('accepts a shape-preserving edit and writes to the fixture', async () => {
    const before = fs.readFileSync(path.join(fixtureRoot, 'registry/SKILL_REGISTRY.md'), 'utf8');
    const edited = before.replace('# Skills Registry', '# Skills Registry (edited)');
    const res = await request(app).put('/api/registry/SKILL_REGISTRY.md').send({ raw: edited });
    expect(res.status).toBe(200);
    expect(res.body.ok).toBe(true);
    const after = fs.readFileSync(path.join(fixtureRoot, 'registry/SKILL_REGISTRY.md'), 'utf8');
    expect(after).toContain('# Skills Registry (edited)');
  });

  it('rejects a dropped column with 422', async () => {
    const before = fs.readFileSync(path.join(fixtureRoot, 'registry/SKILL_REGISTRY.md'), 'utf8');
    // Strip the final column from the header + separator → shape mismatch.
    const broken = before
      .replace('| Skill | Description | Status | Consumers |', '| Skill | Description | Status |')
      .replace('|------|-------------|--------|-----------|', '|------|-------------|--------|');
    const res = await request(app).put('/api/registry/SKILL_REGISTRY.md').send({ raw: broken });
    expect(res.status).toBe(422);
    expect(res.body.error).toMatch(/column/i);
  });

  it('rejects an empty body with 400', async () => {
    const res = await request(app).put('/api/registry/SKILL_REGISTRY.md').send({ raw: '' });
    expect(res.status).toBe(400);
  });
});

describe('GET /api/taxonomy', () => {
  it('lists SKILL_TAXONOMY.md and a *_VOCABULARY.md', async () => {
    const res = await request(app).get('/api/taxonomy');
    expect(res.status).toBe(200);
    const names = res.body.files.map((f: { name: string }) => f.name);
    expect(names).toContain('SKILL_TAXONOMY.md');
    expect(names).toContain('SKILL_VOCABULARY.md');
    const tax = res.body.files.find((f: { name: string }) => f.name === 'SKILL_TAXONOMY.md');
    expect(tax.kind).toBe('taxonomy');
  });
});

describe('GET/PUT /api/taxonomy/:name', () => {
  it('returns raw and accepts a non-empty edit', async () => {
    const get = await request(app).get('/api/taxonomy/SKILL_TAXONOMY.md');
    expect(get.status).toBe(200);
    expect(typeof get.body.raw).toBe('string');

    const edited = get.body.raw + '\n<!-- edited -->\n';
    const put = await request(app).put('/api/taxonomy/SKILL_TAXONOMY.md').send({ raw: edited });
    expect(put.status).toBe(200);
    const after = fs.readFileSync(path.join(fixtureRoot, 'taxonomy/SKILL_TAXONOMY.md'), 'utf8');
    expect(after).toContain('<!-- edited -->');
  });

  it('rejects an empty body with 400', async () => {
    const res = await request(app).put('/api/taxonomy/SKILL_TAXONOMY.md').send({ raw: '   ' });
    expect(res.status).toBe(400);
  });
});
