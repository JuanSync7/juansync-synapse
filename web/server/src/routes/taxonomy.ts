// Taxonomy editing API (FR3.2). Lists taxonomy/*.md AND registry/*_VOCABULARY.md
// (vocabularies are taxonomy-class editables that physically live in registry/),
// serves raw markdown, and writes edits back through safeWrite with an allow-list
// covering both taxonomy/ and registry/. No table-shape guard — these are
// prose+tables — but empty bodies are rejected. :name is resolved against the
// known listing, never interpolated into a path (defense in depth).
import fs from 'node:fs';
import path from 'node:path';
import { Router } from 'express';
import type { Router as ExpressRouter } from 'express';
import type { TaxonomyFile } from '../../../shared/types';
import { safeWrite } from '../lib/safeWrite';

const TAXONOMY_DIR = 'taxonomy';
const REGISTRY_DIR = 'registry';
const ALLOW_DIRS = [TAXONOMY_DIR, REGISTRY_DIR];

/** List taxonomy/*.md (README excluded) plus registry/*_VOCABULARY.md. */
function listTaxonomyFiles(repoRoot: string): TaxonomyFile[] {
  const out: TaxonomyFile[] = [];

  const taxDir = path.join(repoRoot, TAXONOMY_DIR);
  try {
    for (const e of fs.readdirSync(taxDir, { withFileTypes: true })) {
      if (e.isFile() && e.name.endsWith('.md') && e.name !== 'README.md') {
        out.push({ name: e.name, path: `${TAXONOMY_DIR}/${e.name}`, kind: 'taxonomy' });
      }
    }
  } catch {
    /* taxonomy/ absent — fine */
  }

  const regDir = path.join(repoRoot, REGISTRY_DIR);
  try {
    for (const e of fs.readdirSync(regDir, { withFileTypes: true })) {
      if (e.isFile() && /_VOCABULARY\.md$/.test(e.name)) {
        out.push({ name: e.name, path: `${REGISTRY_DIR}/${e.name}`, kind: 'vocabulary' });
      }
    }
  } catch {
    /* registry/ absent — fine */
  }

  return out.sort((a, b) => a.name.localeCompare(b.name));
}

export function taxonomyRouter(repoRoot: string): ExpressRouter {
  const router = Router();

  // GET /api/taxonomy — list of taxonomy + vocabulary files.
  router.get('/', (_req, res) => {
    res.json({ files: listTaxonomyFiles(repoRoot) });
  });

  // GET /api/taxonomy/:name — raw markdown.
  router.get('/:name', (req, res) => {
    const file = listTaxonomyFiles(repoRoot).find((f) => f.name === req.params.name);
    if (!file) {
      res.status(404).json({ error: `No taxonomy file: ${req.params.name}` });
      return;
    }
    let raw: string;
    try {
      raw = fs.readFileSync(path.join(repoRoot, file.path), 'utf8');
    } catch {
      res.status(404).json({ error: `No taxonomy file: ${req.params.name}` });
      return;
    }
    res.json({ name: file.name, raw });
  });

  // PUT /api/taxonomy/:name — write full raw back (allow-list, non-empty body).
  router.put('/:name', (req, res) => {
    const file = listTaxonomyFiles(repoRoot).find((f) => f.name === req.params.name);
    if (!file) {
      res.status(404).json({ error: `No taxonomy file: ${req.params.name}` });
      return;
    }
    const raw = (req.body as { raw?: unknown }).raw;
    if (typeof raw !== 'string' || raw.trim() === '') {
      res.status(400).json({ error: 'Body must include non-empty `raw` string.' });
      return;
    }
    try {
      safeWrite(repoRoot, file.path, raw, ALLOW_DIRS);
    } catch (err) {
      res.status(400).json({ error: err instanceof Error ? err.message : 'Write failed.' });
      return;
    }
    res.json({ ok: true });
  });

  return router;
}
