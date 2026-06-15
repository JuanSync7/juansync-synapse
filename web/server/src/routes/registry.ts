// Registry editing API (FR3.1). Lists the registry/*.md inventory files, serves
// each with its parsed table + raw markdown, and writes edits back through
// safeWrite (registry/ allow-list only) with a same-shape guard so a malformed
// edit that drops/renames a table column is rejected (422) rather than silently
// corrupting the registry. :name is resolved against the known listing — never
// interpolated into a path — as defense in depth on top of safeWrite.
import fs from 'node:fs';
import path from 'node:path';
import { Router } from 'express';
import type { Router as ExpressRouter } from 'express';
import type { RegistryFile } from '../../../shared/types';
import { parseMdTable, sameShape } from '../lib/mdTable';
import { safeWrite } from '../lib/safeWrite';
import { invalidateCache } from '../lib/crawler';

const REGISTRY_DIR = 'registry';

/** List registry/*.md files (README excluded), tagging vocabularies. */
function listRegistryFiles(repoRoot: string): RegistryFile[] {
  const dir = path.join(repoRoot, REGISTRY_DIR);
  let entries: fs.Dirent[];
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return [];
  }
  return entries
    .filter((e) => e.isFile() && e.name.endsWith('.md') && e.name !== 'README.md')
    .map((e) => ({
      name: e.name,
      path: `${REGISTRY_DIR}/${e.name}`,
      kind: /_VOCABULARY\.md$/.test(e.name) ? ('vocabulary' as const) : ('registry' as const),
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

export function registryRouter(repoRoot: string): ExpressRouter {
  const router = Router();

  // GET /api/registry — list of registry files.
  router.get('/', (_req, res) => {
    res.json({ files: listRegistryFiles(repoRoot) });
  });

  // GET /api/registry/:name — raw + parsed table (table:null when not a clean table).
  router.get('/:name', (req, res) => {
    const file = listRegistryFiles(repoRoot).find((f) => f.name === req.params.name);
    if (!file) {
      res.status(404).json({ error: `No registry file: ${req.params.name}` });
      return;
    }
    let raw: string;
    try {
      raw = fs.readFileSync(path.join(repoRoot, file.path), 'utf8');
    } catch {
      res.status(404).json({ error: `No registry file: ${req.params.name}` });
      return;
    }
    const parsed = parseMdTable(raw);
    const table = parsed ? { headers: parsed.headers, rows: parsed.rows } : null;
    res.json({ name: file.name, raw, table });
  });

  // PUT /api/registry/:name — write full raw back, guarding table shape.
  router.put('/:name', (req, res) => {
    const file = listRegistryFiles(repoRoot).find((f) => f.name === req.params.name);
    if (!file) {
      res.status(404).json({ error: `No registry file: ${req.params.name}` });
      return;
    }
    const raw = (req.body as { raw?: unknown }).raw;
    if (typeof raw !== 'string' || raw.trim() === '') {
      res.status(400).json({ error: 'Body must include non-empty `raw` string.' });
      return;
    }

    const abs = path.join(repoRoot, file.path);
    const original = fs.readFileSync(abs, 'utf8');

    // If the original parsed as a table, the edit must preserve its column shape.
    if (parseMdTable(original) && !sameShape(original, raw)) {
      res.status(422).json({
        error:
          'Edit rejected: the table must keep the same columns (same count and names). ' +
          'A column was dropped, added, or renamed.',
      });
      return;
    }

    try {
      safeWrite(repoRoot, file.path, raw, [REGISTRY_DIR]);
    } catch (err) {
      res.status(400).json({ error: err instanceof Error ? err.message : 'Write failed.' });
      return;
    }
    invalidateCache();
    res.json({ ok: true });
  });

  return router;
}
