import { afterEach, describe, expect, it } from 'vitest';
import request from 'supertest';
import { createApp } from '../src/app';
import { resolveRepoRoot } from '../src/repo';
import { invalidateCache } from '../src/lib/crawler';

const app = createApp(resolveRepoRoot());

afterEach(() => invalidateCache());

describe('GET /api/scripts', () => {
  it('lists scripts including validate with an audience, plus cli-commands', async () => {
    const res = await request(app).get('/api/scripts');
    expect(res.status).toBe(200);
    const names = res.body.scripts.map((s: { name: string }) => s.name);
    expect(names).toContain('validate');
    const validate = res.body.scripts.find((s: { name: string }) => s.name === 'validate');
    expect(validate.audience).toBeTruthy();
    expect(validate.kind).toBe('script');
    // cli-commands surfaced from docs/cli without a matching .sh.
    const cli = res.body.cliCommands.map((c: { name: string }) => c.name);
    expect(cli).toContain('drift');
    expect(cli).not.toContain('validate');
  });
});

describe('POST /api/scripts/run', () => {
  it('rejects a non-allow-listed command with 400 and does not run it', async () => {
    const res = await request(app)
      .post('/api/scripts/run')
      .send({ command: './cortex', args: ['clean'] });
    expect(res.status).toBe(400);
    expect(res.body.error).toBeTruthy();
  });

  it('rejects a non-cortex command with 400', async () => {
    const res = await request(app)
      .post('/api/scripts/run')
      .send({ command: 'rm', args: ['-rf', '/'] });
    expect(res.status).toBe(400);
  });

  it('runs an allow-listed read-only command and returns an exit code', async () => {
    const res = await request(app)
      .post('/api/scripts/run')
      .send({ command: './cortex', args: ['available'] });
    expect(res.status).toBe(200);
    expect(typeof res.body.exitCode).toBe('number');
    expect(typeof res.body.stdout).toBe('string');
  });
});

describe('GET /api/framework', () => {
  it('returns groups of base skills including the creator, plus a lifecycle array', async () => {
    const res = await request(app).get('/api/framework');
    expect(res.status).toBe(200);
    const skillSlugs = res.body.groups.skills.map((s: { slug: string }) => s.slug);
    expect(skillSlugs).toContain('synapse-router-artifact-creator');
    // every grouped skill is base layer (synapse/).
    expect(Array.isArray(res.body.lifecycle)).toBe(true);
    expect(res.body.lifecycle.length).toBeGreaterThan(0);
    const labels = res.body.lifecycle.map((l: { label: string }) => l.label);
    expect(labels).toContain('creator');
    const creatorStep = res.body.lifecycle.find((l: { label: string }) => l.label === 'creator');
    expect(creatorStep.slug).toBe('synapse-router-artifact-creator');
  });
});
