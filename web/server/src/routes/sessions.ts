// Headless brainstorm/session API (FR6). The route is a thin shell over the
// claudeSession driver: it owns HTTP shapes and the SSE wire protocol; the
// driver owns process lifecycle, parsing, and persistence.
//
// SSE design (DESIGN.md decision #4): GET /:id/events first REPLAYS any lines
// already captured to the transcript, then attaches to the live emitter and
// streams new events. One watcher leaving does NOT kill a still-running session
// (req close just detaches the listener); only POST /:id/abort kills it.
import { Router } from 'express';
import type { Request, Response, Router as ExpressRouter } from 'express';
import type { SessionEvent } from '../../../shared/types';
import {
  defaultSessionDir,
  getActiveSession,
  killSession,
  listSessions,
  readMeta,
  readTranscript,
  resumeSession,
  startSession,
} from '../lib/claudeSession';

const BRAINSTORM_SKILL = 'synapse-router-artifact-brainstormer';

/** Build the effective prompt: `/<skill> <message>`, or raw when no skill. */
function effectivePrompt(message: string, skill?: string): string {
  if (skill && skill !== '') return `/${skill} ${message}`;
  return message;
}

/** Write one SSE frame: `event: <type>\ndata: <json>\n\n`. */
function writeFrame(res: Response, event: SessionEvent): void {
  res.write(`event: ${event.type}\n`);
  res.write(`data: ${JSON.stringify(event.data)}\n\n`);
}

export function sessionsRouter(repoRoot: string): ExpressRouter {
  const router = Router();
  const sessionDir = defaultSessionDir(repoRoot);

  // POST /api/sessions { message, skill? } — start a brainstorm session.
  router.post('/', (req, res) => {
    const body = (req.body ?? {}) as { message?: unknown; skill?: unknown };
    if (typeof body.message !== 'string' || body.message.trim() === '') {
      res.status(400).json({ error: 'Body must include a non-empty `message`.' });
      return;
    }
    const skill = typeof body.skill === 'string' && body.skill !== '' ? body.skill : BRAINSTORM_SKILL;
    const prompt = effectivePrompt(body.message, skill);
    const session = startSession({ repoRoot, prompt, sessionDir, title: body.message.trim() });
    res.json({ id: session.id });
  });

  // GET /api/sessions — list persisted sessions (FR6.3).
  router.get('/', (_req, res) => {
    res.json({ sessions: listSessions(sessionDir) });
  });

  // GET /api/sessions/:id — meta + full transcript for reload (FR6.4).
  router.get('/:id', (req, res) => {
    const id = req.params.id ?? '';
    const meta = readMeta(sessionDir, id);
    if (!meta) {
      res.status(404).json({ error: `No session: ${id}` });
      return;
    }
    res.json({ meta, events: readTranscript(sessionDir, id) });
  });

  // GET /api/sessions/:id/events — SSE: replay captured lines, then stream live.
  router.get('/:id/events', (req: Request, res: Response) => {
    const id = req.params.id ?? '';
    const meta = readMeta(sessionDir, id);
    if (!meta) {
      res.status(404).json({ error: `No session: ${id}` });
      return;
    }

    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    });
    res.flushHeaders?.();

    // 1. Replay everything already captured to the transcript.
    for (const event of readTranscript(sessionDir, id)) {
      writeFrame(res, event);
    }

    const active = getActiveSession(id);
    if (!active) {
      // Already finished before this watcher attached — emit a terminal frame
      // so the client stops waiting, then close.
      writeFrame(res, { type: 'exit', data: { status: meta.status, replayed: true } });
      res.end();
      return;
    }

    // 2. Attach to the live emitter and stream new events until exit/result.
    const onEvent = (event: SessionEvent) => {
      writeFrame(res, event);
      if (event.type === 'exit') {
        cleanup();
        res.end();
      }
    };
    const cleanup = () => {
      active.emitter.off('event', onEvent);
    };
    active.emitter.on('event', onEvent);

    // A watcher disconnecting only DETACHES — it never kills a running session
    // (another tab or a later GET /:id may still want the output).
    req.on('close', cleanup);
  });

  // POST /api/sessions/:id/messages { message } — resume with a new turn.
  router.post('/:id/messages', (req, res) => {
    const id = req.params.id ?? '';
    const body = (req.body ?? {}) as { message?: unknown };
    if (typeof body.message !== 'string' || body.message.trim() === '') {
      res.status(400).json({ error: 'Body must include a non-empty `message`.' });
      return;
    }
    const meta = readMeta(sessionDir, id);
    if (!meta) {
      res.status(404).json({ error: `No session: ${id}` });
      return;
    }
    if (!meta.claudeSessionId) {
      res.status(409).json({ error: 'Session has no claude session id yet — cannot resume.' });
      return;
    }
    resumeSession({
      repoRoot,
      prompt: body.message,
      claudeSessionId: meta.claudeSessionId,
      id,
      sessionDir,
    });
    res.json({ ok: true });
  });

  // POST /api/sessions/:id/abort — explicit kill (the only thing that kills).
  router.post('/:id/abort', (req, res) => {
    const killed = killSession(req.params.id ?? '');
    res.json({ ok: killed });
  });

  return router;
}
