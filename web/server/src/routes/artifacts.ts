import fs from 'node:fs';
import path from 'node:path';
import { Router } from 'express';
import type { Router as ExpressRouter } from 'express';
import type {
  Artifact,
  ArtifactClass,
  ArtifactDetail,
  Companion,
  Counts,
  EvalData,
} from '../../../shared/types';
import { getIndex, matchRegistryRow, resolvePathway } from '../lib/crawler';
import { parseEval } from '../lib/evalParse';
import { parseFrontmatter } from '../lib/frontmatter';

const VALID_CLASSES: readonly ArtifactClass[] = ['skill', 'agent', 'protocol', 'tool', 'pathway'];

// Registry file backing each class (under registry/). Used for registryRow.
const REGISTRY_FILE: Record<ArtifactClass, string> = {
  skill: 'SKILL_REGISTRY.md',
  agent: 'AGENTS_REGISTRY.md',
  protocol: 'PROTOCOL_REGISTRY.md',
  tool: 'TOOL_REGISTRY.md',
  pathway: 'PATHWAY_REGISTRY.md',
};

function isValidClass(v: string): v is ArtifactClass {
  return (VALID_CLASSES as readonly string[]).includes(v);
}

function countsOf(index: Artifact[]): Counts {
  const counts: Counts = { skill: 0, agent: 0, protocol: 0, tool: 0, pathway: 0 };
  for (const a of index) counts[a.class] += 1;
  return counts;
}

export function artifactsRouter(repoRoot: string): ExpressRouter {
  const router = Router();

  // GET /api/artifacts — filterable list + unfiltered per-class counts.
  router.get('/', (req, res) => {
    const index = getIndex(repoRoot);
    const counts = countsOf(index);

    const classQ = typeof req.query.class === 'string' ? req.query.class : undefined;
    if (classQ !== undefined && !isValidClass(classQ)) {
      res.status(400).json({ error: `Unknown artifact class: ${classQ}` });
      return;
    }

    const q = typeof req.query.q === 'string' ? req.query.q.toLowerCase() : undefined;
    const layer = typeof req.query.layer === 'string' ? req.query.layer : undefined;
    const domain = typeof req.query.domain === 'string' ? req.query.domain : undefined;

    const items = index.filter((a) => {
      if (classQ && a.class !== classQ) return false;
      if (layer && a.layer !== layer) return false;
      if (domain && a.domain !== domain) return false;
      if (q) {
        const hay = `${a.slug} ${a.description ?? ''}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    res.json({ items, counts });
  });

  // GET /api/artifacts/:class/:slug — full detail.
  router.get('/:class/:slug', (req, res) => {
    const cls = req.params.class;
    if (!isValidClass(cls)) {
      res.status(400).json({ error: `Unknown artifact class: ${cls}` });
      return;
    }

    const index = getIndex(repoRoot);
    const item = index.find((a) => a.class === cls && a.slug === req.params.slug);
    if (!item) {
      res.status(404).json({ error: `No ${cls} with slug: ${req.params.slug}` });
      return;
    }

    const absPath = path.join(repoRoot, item.path);
    // Strip the leading YAML frontmatter — it is surfaced structurally in the
    // detail page's right rail (Frontmatter card). Rendering it inline dumps the
    // raw `--- … ---` block at the top of the body, where react-markdown turns
    // the closing `---` into a setext heading (a giant bold blob). The body
    // should be clean prose only.
    const body = parseFrontmatter(readFile(absPath)).body.replace(/^\s+/, '');

    const detail: ArtifactDetail = {
      item,
      body,
      eval: loadEval(item, absPath),
      companions: collectCompanions(item, absPath, repoRoot),
      registryRow: loadRegistryRow(repoRoot, cls, item.slug),
      pathwayResolved: cls === 'pathway' ? resolvePathway(repoRoot, item.slug) : null,
    };

    res.json(detail);
  });

  return router;
}

function loadEval(item: Artifact, absPath: string): EvalData | null {
  // skills/tools: EVAL.md sibling; agents/protocols: <basename>.eval.md sibling.
  let evalPath: string | null = null;
  if (item.class === 'skill' || item.class === 'tool') {
    evalPath = path.join(path.dirname(absPath), 'EVAL.md');
  } else if (item.class === 'agent' || item.class === 'protocol') {
    evalPath = absPath.replace(/\.md$/, '.eval.md');
  }
  if (!evalPath || !fs.existsSync(evalPath)) return null;
  return parseEval(readFile(evalPath));
}

function loadRegistryRow(
  repoRoot: string,
  cls: ArtifactClass,
  slug: string,
): Record<string, string> | null {
  const file = path.join(repoRoot, 'registry', REGISTRY_FILE[cls]);
  if (!fs.existsSync(file)) return null;
  return matchRegistryRow(readFile(file), slug);
}

// Companion subtrees/files we surface alongside a skill or tool (FR1.2).
function collectCompanions(item: Artifact, absPath: string, repoRoot: string): Companion[] {
  if (item.class !== 'skill' && item.class !== 'tool') return [];
  const dir = path.dirname(absPath);
  const companions: Companion[] = [];

  addDir(path.join(dir, 'references'), 'reference', repoRoot, companions);
  addDir(path.join(dir, 'templates'), 'template', repoRoot, companions);

  // Top-level schema*/cli* files (e.g. schemas.py, cli.py) beside the manifest.
  let entries: fs.Dirent[];
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    entries = [];
  }
  for (const e of entries) {
    if (!e.isFile()) continue;
    const lower = e.name.toLowerCase();
    if (lower.startsWith('schema')) {
      companions.push(makeCompanion(repoRoot, path.join(dir, e.name), 'schema'));
    } else if (lower.startsWith('cli')) {
      companions.push(makeCompanion(repoRoot, path.join(dir, e.name), 'cli'));
    }
  }

  return companions;
}

function addDir(
  dir: string,
  kind: Companion['kind'],
  repoRoot: string,
  out: Companion[],
): void {
  let entries: fs.Dirent[];
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const e of entries) {
    if (e.isFile()) out.push(makeCompanion(repoRoot, path.join(dir, e.name), kind));
  }
}

function makeCompanion(repoRoot: string, abs: string, kind: Companion['kind']): Companion {
  return {
    name: path.basename(abs),
    path: path.relative(repoRoot, abs).split(path.sep).join('/'),
    kind,
  };
}

function readFile(file: string): string {
  try {
    return fs.readFileSync(file, 'utf8');
  } catch {
    return '';
  }
}
