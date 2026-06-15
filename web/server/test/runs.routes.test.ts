// Integration tests for the creator-run routes (FR7). NEVER spawns real claude
// (CLAUDE_BIN → fake) and NEVER runs the real validate: the repoRoot is a TEMP
// git repo with a `cortex` stub that exits 0. The fake claude creates a file so
// the git-diff verification path is exercised for real. SSE is read over a real
// app.listen(0) socket (the S8 technique).
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import request from 'supertest';
import { createApp } from '../src/app';

const here = path.dirname(fileURLToPath(import.meta.url));
const FAKE = path.join(here, 'fixtures', 'fake-claude.mjs');

let repoRoot: string;
let app: ReturnType<typeof createApp>;
let memoId: string;
const savedBin = process.env.CLAUDE_BIN;
const savedCreate = process.env.FAKE_CLAUDE_CREATE_FILE;

beforeEach(() => {
  repoRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'synapse-run-routes-'));
  execFileSync('git', ['init', '-q'], { cwd: repoRoot });
  execFileSync('git', ['config', 'user.email', 't@t.t'], { cwd: repoRoot });
  execFileSync('git', ['config', 'user.name', 'tester'], { cwd: repoRoot });

  const memoDir = path.join(repoRoot, 'src', 'tools', 'demo', 'change_requests');
  fs.mkdirSync(memoDir, { recursive: true });
  const memoRel = 'src/tools/demo/change_requests/2026-06-13-tool.md';
  fs.writeFileSync(path.join(repoRoot, memoRel), '# Tool memo\n\nbody\n', 'utf8');

  // Mirror the real repo: web/.sessions is gitignored, so the run store never
  // shows up as a "created path" in the verification diff.
  fs.writeFileSync(path.join(repoRoot, '.gitignore'), 'web/\n', 'utf8');

  const cortex = path.join(repoRoot, 'cortex');
  fs.writeFileSync(cortex, '#!/usr/bin/env bash\necho "0 errors / 0 warnings"\nexit 0\n', 'utf8');
  fs.chmodSync(cortex, 0o755);

  execFileSync('git', ['add', '-A'], { cwd: repoRoot });
  execFileSync('git', ['commit', '-q', '-m', 'baseline'], { cwd: repoRoot });

  // Fake claude creates an artifact so verification sees a change.
  process.env.FAKE_CLAUDE_CREATE_FILE = path.join(
    repoRoot,
    'src',
    'tools',
    'demo',
    'demo-tool',
    'TOOL.md',
  );
  process.env.CLAUDE_BIN = FAKE;
  memoId = memoRel.replace(/\.md$/, '').split('/').join('__');
  app = createApp(repoRoot);
});

afterEach(() => {
  fs.rmSync(repoRoot, { recursive: true, force: true });
  if (savedBin === undefined) delete process.env.CLAUDE_BIN;
  else process.env.CLAUDE_BIN = savedBin;
  if (savedCreate === undefined) delete process.env.FAKE_CLAUDE_CREATE_FILE;
  else process.env.FAKE_CLAUDE_CREATE_FILE = savedCreate;
});

/** Poll the run detail until it reaches a terminal status (or times out). */
async function waitForTerminal(id: string, ms = 6000): Promise<string> {
  const deadline = Date.now() + ms;
  for (;;) {
    const res = await request(app).get(`/api/runs/${id}`);
    if (res.status === 200 && res.body.meta.status !== 'running') return res.body.meta.status;
    if (Date.now() > deadline) throw new Error('run never reached terminal status');
    await new Promise((r) => setTimeout(r, 50));
  }
}

/** Read a full SSE stream over a real socket against a listening server. */
function readSse(server: http.Server, urlPath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const addr = server.address();
    if (!addr || typeof addr === 'string') {
      reject(new Error('server not listening'));
      return;
    }
    const req = http.request(
      { host: '127.0.0.1', port: addr.port, path: urlPath, method: 'GET' },
      (res) => {
        let buf = '';
        res.setEncoding('utf8');
        res.on('data', (c) => {
          buf += c;
        });
        res.on('end', () => resolve(buf));
      },
    );
    req.on('error', reject);
    req.end();
  });
}

describe('POST /api/runs/creator + lifecycle', () => {
  it('starts a run, lists it, returns status + verification', async () => {
    const start = await request(app).post('/api/runs/creator').send({ memoId });
    expect(start.status).toBe(200);
    const id = start.body.id as string;
    expect(id).toBeTruthy();

    const status = await waitForTerminal(id);
    expect(status).toBe('succeeded');

    const list = await request(app).get('/api/runs');
    expect(list.status).toBe(200);
    expect(list.body.runs.some((r: { id: string }) => r.id === id)).toBe(true);

    const detail = await request(app).get(`/api/runs/${id}`);
    expect(detail.status).toBe(200);
    expect(detail.body.meta.status).toBe('succeeded');
    expect(detail.body.verification.validate.exitCode).toBe(0);
    const created = detail.body.verification.createdPaths.map((c: { path: string }) => c.path);
    expect(created).toContain('src/tools/demo/demo-tool/TOOL.md');
    // Transcript carries the fake claude output.
    expect(JSON.stringify(detail.body.events)).toContain('Done from fake claude.');
  });

  it('404s an unknown memo and 400s a missing memoId', async () => {
    const unknown = await request(app).post('/api/runs/creator').send({ memoId: 'nope' });
    expect(unknown.status).toBe(404);
    const missing = await request(app).post('/api/runs/creator').send({});
    expect(missing.status).toBe(400);
    const missingRun = await request(app).get('/api/runs/no-such-id');
    expect(missingRun.status).toBe(404);
  });

  it('GET /:id/events streams session events + a final verification frame', async () => {
    const start = await request(app).post('/api/runs/creator').send({ memoId });
    const id = start.body.id as string;
    await waitForTerminal(id);

    const server = app.listen(0);
    try {
      const body = await readSse(server, `/api/runs/${id}/events`);
      // Session events replayed.
      expect(body).toContain('event: assistant');
      expect(body).toContain('Hello from fake claude.');
      expect(body).toContain('event: result');
      // The terminal verification frame carries createdPaths + validate.
      expect(body).toContain('event: verification');
      expect(body).toContain('demo-tool/TOOL.md');
      expect(body).toContain('event: exit');
    } finally {
      server.close();
    }
  });
});
