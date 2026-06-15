// Creator end-to-end run API (FR7). A thin HTTP/SSE shell over the creatorRun
// driver: it owns request shapes and the SSE wire protocol; the driver owns the
// session lifecycle, the git-diff + validate verification, and persistence.
//
// SSE design (mirrors the sessions route, DESIGN.md decision #4): GET /:id/events
// REPLAYS the underlying session's captured transcript, then streams live
// session events; after the claude session ends it emits ONE terminal
// 'verification' frame carrying {createdPaths, validate} so the run page can
// render its panel without a second request. A watcher disconnecting only
// detaches; only POST /:id/abort kills the run.
import { Router } from 'express';
import type { Request, Response, Router as ExpressRouter } from 'express';
import type { RunVerification, SessionEvent } from '../../../shared/types';
import { defaultSessionDir } from '../lib/claudeSession';
import {
  abortRun,
  getActiveRun,
  getRun,
  listRuns,
  readRunTranscript,
  readVerification,
  startCreatorRun,
} from '../lib/creatorRun';

/** Write one SSE frame: `event: <type>\ndata: <json>\n\n`. */
function writeFrame(res: Response, type: string, data: unknown): void {
  res.write(`event: ${type}\n`);
  res.write(`data: ${JSON.stringify(data)}\n\n`);
}

export function runsRouter(repoRoot: string): ExpressRouter {
  const router = Router();
  const sessionDir = defaultSessionDir(repoRoot);

  // POST /api/runs/creator { memoId } — start a creator end-to-end run (FR7.1).
  router.post('/creator', (req, res) => {
    const body = (req.body ?? {}) as { memoId?: unknown };
    if (typeof body.memoId !== 'string' || body.memoId.trim() === '') {
      res.status(400).json({ error: 'Body must include a non-empty `memoId`.' });
      return;
    }
    startCreatorRun({ repoRoot, memoId: body.memoId, sessionDir })
      .then((run) => res.json({ id: run.id }))
      .catch((err: Error & { code?: string }) => {
        if (err.code === 'NOT_FOUND') {
          res.status(404).json({ error: err.message });
        } else {
          res.status(500).json({ error: err.message });
        }
      });
  });

  // GET /api/runs — list persisted runs (FR7.3).
  router.get('/', (_req, res) => {
    res.json({ runs: listRuns(sessionDir) });
  });

  // GET /api/runs/:id — meta + transcript + verification (when complete).
  router.get('/:id', (req, res) => {
    const id = req.params.id ?? '';
    const meta = getRun(sessionDir, id);
    if (!meta) {
      res.status(404).json({ error: `No run: ${id}` });
      return;
    }
    res.json({
      meta,
      events: readRunTranscript(sessionDir, id),
      verification: readVerification(sessionDir, id),
    });
  });

  // GET /api/runs/:id/events — SSE: replay transcript, stream live, then a final
  // 'verification' frame once the run completes its git-diff + validate.
  router.get('/:id/events', (req: Request, res: Response) => {
    const id = req.params.id ?? '';
    const meta = getRun(sessionDir, id);
    if (!meta) {
      res.status(404).json({ error: `No run: ${id}` });
      return;
    }

    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    });
    res.flushHeaders?.();

    // 1. Replay everything already captured to the session transcript — EXCEPT
    //    the session's intrinsic 'exit' event. A run defines its OWN terminal
    //    'exit' frame, emitted only AFTER verification; if we forwarded the
    //    session-level exit the client would close the stream before the
    //    'verification' frame arrived and never render the panel.
    for (const event of readRunTranscript(sessionDir, id)) {
      if (event.type === 'exit') continue;
      writeFrame(res, event.type, event.data);
    }

    const active = getActiveRun(id);
    if (!active) {
      // Already finished before this watcher attached — emit the persisted
      // verification (if any) and a terminal exit frame, then close.
      const verification = readVerification(sessionDir, id);
      const finalMeta = getRun(sessionDir, id);
      if (verification) writeFrame(res, 'verification', verification);
      writeFrame(res, 'exit', { status: finalMeta?.status ?? meta.status, replayed: true });
      res.end();
      return;
    }

    // 2. Attach live: forward session events; on the session exit, wait for the
    //    verification event, emit it, then close.
    const onSessionEvent = (event: SessionEvent) => {
      // Swallow the session's intrinsic exit — the run's terminal 'exit' frame is
      // emitted by onVerification, after the git-diff + validate complete. (See
      // the replay note above: a premature exit closes the client stream early.)
      if (event.type === 'exit') return;
      writeFrame(res, event.type, event.data);
    };
    const onVerification = (verification: RunVerification) => {
      writeFrame(res, 'verification', verification);
      const finalMeta = getRun(sessionDir, id);
      writeFrame(res, 'exit', { status: finalMeta?.status ?? 'failed' });
      cleanup();
      res.end();
    };
    const cleanup = () => {
      active.emitter.off('session-event', onSessionEvent);
      active.emitter.off('verification', onVerification);
    };
    active.emitter.on('session-event', onSessionEvent);
    active.emitter.on('verification', onVerification);

    req.on('close', cleanup);
  });

  // POST /api/runs/:id/abort — kill the underlying claude session (NFR5).
  router.post('/:id/abort', (req, res) => {
    const killed = abortRun(sessionDir, req.params.id ?? '');
    res.json({ ok: killed });
  });

  return router;
}
