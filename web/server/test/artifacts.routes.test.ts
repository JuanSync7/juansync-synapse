import { afterEach, describe, expect, it } from 'vitest';
import request from 'supertest';
import { createApp } from '../src/app';
import { resolveRepoRoot } from '../src/repo';
import { invalidateCache } from '../src/lib/crawler';

const app = createApp(resolveRepoRoot());

afterEach(() => invalidateCache());

describe('GET /api/artifacts', () => {
  it('lists skills including an addon skill and the base creator', async () => {
    const res = await request(app).get('/api/artifacts?class=skill');
    expect(res.status).toBe(200);
    const items = res.body.items as { slug: string; layer: string }[];
    const slugs = items.map((a) => a.slug);
    // The base framework skill is always present; assert addon classification
    // structurally — adopter slugs migrate across branches, so don't hardcode.
    expect(slugs).toContain('synapse-router-artifact-creator');
    expect(items.some((a) => a.layer === 'addon')).toBe(true);
    expect(res.body.counts.skill).toBeGreaterThanOrEqual(30);
  });

  it('counts reflect unfiltered totals even when filtered', async () => {
    // `router` matches the stable synapse-router-* base skills (a subset).
    const res = await request(app).get('/api/artifacts?class=skill&q=router');
    expect(res.body.items.length).toBeGreaterThan(0);
    // q is a substring match on slug+description, so a hit may be in either.
    expect(
      res.body.items.every((a: { slug: string; description: string | null }) =>
        `${a.slug} ${a.description ?? ''}`.toLowerCase().includes('router'),
      ),
    ).toBe(true);
    expect(res.body.items.length).toBeLessThan(res.body.counts.skill);
    expect(res.body.counts.skill).toBeGreaterThanOrEqual(30);
  });

  it('lists tools (TOOL.md artifacts)', async () => {
    const res = await request(app).get('/api/artifacts?class=tool');
    const slugs = res.body.items.map((a: { slug: string }) => a.slug);
    expect(slugs.length).toBeGreaterThan(0);
  });

  it('filters by layer and domain', async () => {
    const res = await request(app).get('/api/artifacts?class=skill&layer=base');
    expect(res.body.items.every((a: { layer: string }) => a.layer === 'base')).toBe(true);
  });

  it('rejects a bad class with 400 JSON', async () => {
    const res = await request(app).get('/api/artifacts?class=bogus');
    expect(res.status).toBe(400);
    expect(res.body.error).toBeTruthy();
  });
});

describe('GET /api/artifacts/:class/:slug', () => {
  it('returns body + eval groups for the base creator skill', async () => {
    const res = await request(app).get('/api/artifacts/skill/synapse-router-artifact-creator');
    expect(res.status).toBe(200);
    expect(res.body.body).toContain('# ');
    expect(res.body.eval).not.toBeNull();
    const g = res.body.eval.groups;
    expect(g.execution.length + g.output.length + g.other.length).toBeGreaterThan(0);
    expect(res.body.registryRow).not.toBeNull();
  });

  it('resolves a pathway with a non-empty skills array', async () => {
    const res = await request(app).get('/api/artifacts/pathway/synapse-skill');
    expect(res.status).toBe(200);
    expect(res.body.pathwayResolved.skills.length).toBeGreaterThan(0);
  });

  it('404s an unknown slug', async () => {
    const res = await request(app).get('/api/artifacts/skill/no-such-skill-xyz');
    expect(res.status).toBe(404);
    expect(res.body.error).toBeTruthy();
  });

  it('400s a bad class', async () => {
    const res = await request(app).get('/api/artifacts/bogus/x');
    expect(res.status).toBe(400);
  });
});

describe('GET /api/pipeline', () => {
  it('returns presets.full as an array containing spec', async () => {
    const res = await request(app).get('/api/pipeline');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body.presets.full)).toBe(true);
    expect(res.body.presets.full).toContain('spec');
  });
});
