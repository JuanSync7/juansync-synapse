// Memo board API (FR5). GET lists memos (optional executed filter) with counts;
// GET /:id returns the memo plus its raw body; PATCH /:id toggles the executed
// frontmatter flag through setMemoExecuted (byte-preserving, allow-listed write,
// NFR5) and invalidates the artifact cache. :id is always resolved against
// crawlMemos — never interpolated into a path — as defense in depth on top of
// safeWrite's allow-list.
import fs from 'node:fs';
import path from 'node:path';
import { Router } from 'express';
import type { Router as ExpressRouter } from 'express';
import { invalidateCache } from '../lib/crawler';
import { crawlMemos, setMemoExecuted } from '../lib/memos';

export function memosRouter(repoRoot: string): ExpressRouter {
  const router = Router();

  // GET /api/memos?executed=true|false — list + counts (filter is display-only;
  // counts always reflect the full set so the UI can show All/Executed/Pending).
  router.get('/', (req, res) => {
    const all = crawlMemos(repoRoot);
    const counts = {
      total: all.length,
      executed: all.filter((m) => m.executed).length,
      pending: all.filter((m) => !m.executed).length,
    };
    const filter = req.query.executed;
    let memos = all;
    if (filter === 'true') memos = all.filter((m) => m.executed);
    else if (filter === 'false') memos = all.filter((m) => !m.executed);
    res.json({ memos, counts });
  });

  // GET /api/memos/:id — memo + raw markdown body.
  router.get('/:id', (req, res) => {
    const memo = crawlMemos(repoRoot).find((m) => m.id === req.params.id);
    if (!memo) {
      res.status(404).json({ error: `No memo: ${req.params.id}` });
      return;
    }
    let body = '';
    if (memo.path) {
      try {
        body = fs.readFileSync(path.join(repoRoot, memo.path), 'utf8');
      } catch {
        body = '';
      }
    }
    res.json({ memo, body });
  });

  // PATCH /api/memos/:id { executed } — toggle the executed flag.
  router.patch('/:id', (req, res) => {
    const body = (req.body ?? {}) as { executed?: unknown };
    if (typeof body.executed !== 'boolean') {
      res.status(400).json({ error: 'Body must include a boolean `executed`.' });
      return;
    }
    // 404 unknown id without leaking the write path.
    const known = crawlMemos(repoRoot).some((m) => m.id === req.params.id);
    if (!known) {
      res.status(404).json({ error: `No memo: ${req.params.id}` });
      return;
    }
    try {
      const updated = setMemoExecuted(repoRoot, req.params.id, body.executed);
      invalidateCache();
      res.json({ memo: updated });
    } catch (err) {
      res.status(400).json({ error: err instanceof Error ? err.message : 'Update failed.' });
    }
  });

  return router;
}
