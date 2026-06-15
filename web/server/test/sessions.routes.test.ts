// Integration tests for the session routes (FR6). NEVER spawns the real claude:
// CLAUDE_BIN points at the fake binary fixture. The repo root is a TEMP dir, so
// the session store lives at <temp>/web/.sessions and the real web/.sessions/
// is never touched.
//
// SSE replay+live coverage:
//  - "streams the canned transcript and closes" uses the FAST fake (exits 0
//    immediately). By the time GET /events runs, the session has finished, so
//    this asserts the REPLAY path (transcript → SSE frames) ends with an exit.
//  - "streams live events from a running session" uses the HANG fake: we attach
//    to /events while the child is still alive, so the assistant/result frames
//    arrive over the LIVE emitter; then POST /abort kills it.
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest';
import request from 'supertest';
import { createApp } from '../src/app';

const here = path.dirname(fileURLToPath(import.meta.url));
const FAKE = path.join(here, 'fixtures', 'fake-claude.mjs');

let repoRoot: string;
let app: ReturnType<typeof createApp>;
const savedBin = process.env.CLAUDE_BIN;

beforeAll(() => {
  repoRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'synapse-sess-routes-'));
  process.env.CLAUDE_BIN = FAKE;
  app = createApp(repoRoot);
});

afterAll(() => {
  fs.rmSync(repoRoot, { recursive: true, force: true });
  if (savedBin === undefined) delete process.env.CLAUDE_BIN;
  else process.env.CLAUDE_BIN = savedBin;
});

afterEach(() => {
  delete process.env.FAKE_CLAUDE_HANG;
});

/** Poll the session meta until it reaches a terminal status (or times out). */
async function waitForStatus(id: string, want: string, ms = 4000): Promise<void> {
  const deadline = Date.now() + ms;
  for (;;) {
    const res = await request(app).get(`/api/sessions/${id}`);
    if (res.status === 200 && res.body.meta.status === want) return;
    if (Date.now() > deadline) throw new Error(`status never reached ${want}`);
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

describe('POST /api/sessions + lifecycle (fast fake)', () => {
  it('starts a session, lists it, returns meta+transcript, and aborts', async () => {
    const start = await request(app)
      .post('/api/sessions')
      .send({ message: 'design a widget', skill: 'synapse-router-artifact-brainstormer' });
    expect(start.status).toBe(200);
    const id = start.body.id as string;
    expect(id).toBeTruthy();

    await waitForStatus(id, 'done');

    // GET /api/sessions lists it.
    const list = await request(app).get('/api/sessions');
    expect(list.status).toBe(200);
    const found = list.body.sessions.find((s: { id: string }) => s.id === id);
    expect(found).toBeDefined();
    expect(found.title).toBe('design a widget');
    expect(found.status).toBe('done');

    // GET /api/sessions/:id returns meta + parsed transcript events.
    const detail = await request(app).get(`/api/sessions/${id}`);
    expect(detail.status).toBe(200);
    expect(detail.body.meta.claudeSessionId).toBe('fake-session-0001');
    const text = JSON.stringify(detail.body.events);
    expect(text).toContain('Hello from fake claude.');
    expect(text).toContain('Done from fake claude.');

    // Abort is a no-op on a finished session but must not error.
    const abort = await request(app).post(`/api/sessions/${id}/abort`);
    expect(abort.status).toBe(200);
    expect(abort.body.ok).toBe(false);
  });

  it('GET /:id/events REPLAYS the captured transcript and closes', async () => {
    const start = await request(app).post('/api/sessions').send({ message: 'replay me' });
    const id = start.body.id as string;
    await waitForStatus(id, 'done');

    // Once finished, the SSE stream replays the transcript then ends.
    const server = app.listen(0);
    try {
      const body = await readSse(server, `/api/sessions/${id}/events`);
      expect(body).toContain('event: assistant');
      expect(body).toContain('Hello from fake claude.');
      expect(body).toContain('event: result');
      expect(body).toContain('Done from fake claude.');
      // Terminal exit frame so the client stops waiting.
      expect(body).toContain('event: exit');
    } finally {
      server.close();
    }
  });

  it('400s an empty message and 404s an unknown id', async () => {
    const bad = await request(app).post('/api/sessions').send({ message: '   ' });
    expect(bad.status).toBe(400);
    const missing = await request(app).get('/api/sessions/no-such-id');
    expect(missing.status).toBe(404);
    const missingEvents = await request(app).get('/api/sessions/no-such-id/events');
    expect(missingEvents.status).toBe(404);
  });
});

describe('GET /:id/events streams LIVE events (hang fake)', () => {
  it('attaches to a running session, streams frames, then abort ends it', async () => {
    process.env.FAKE_CLAUDE_HANG = '1';
    const start = await request(app).post('/api/sessions').send({ message: 'live stream' });
    const id = start.body.id as string;

    const server = app.listen(0);
    try {
      // Attach while the child is still alive (it hangs after emitting lines).
      const ssePromise = readSse(server, `/api/sessions/${id}/events`);
      // Give the SSE handler a moment to attach + flush the early frames.
      await new Promise((r) => setTimeout(r, 200));
      // Abort kills the hanging child → exit frame → stream ends.
      const abort = await request(app).post(`/api/sessions/${id}/abort`);
      expect(abort.body.ok).toBe(true);

      const body = await ssePromise;
      expect(body).toContain('Hello from fake claude.');
      expect(body).toContain('event: exit');
    } finally {
      server.close();
    }

    await waitForStatus(id, 'error');
  });
});
