import fs from 'node:fs';
import path from 'node:path';
import { parse as parseYaml } from 'yaml';
import type { Artifact, ArtifactClass, Layer, ResolvedPathway } from '../../../shared/types';
import { parseFrontmatter } from './frontmatter';

// Directories we never descend into, anywhere in the tree. node_modules/.git
// are noise; web/ is this app (not a synapse artifact tree, NFR7); dist is
// build output; the dot-dirs hold transient session/brainstorm state.
const SKIP_DIRS = new Set(['node_modules', '.git', 'web', 'dist', '.brainstorms', '.delivery']);

const CACHE_TTL_MS = 60_000;

interface CacheEntry {
  index: Artifact[];
  builtAt: number;
}
let cache: CacheEntry | null = null;

/** Drop the in-memory index so the next request re-crawls (FR1.1, testing). */
export function invalidateCache(): void {
  cache = null;
}

/**
 * Return the artifact index, using a 60s in-memory cache. The repo is the
 * database (DESIGN.md decision #1): crawling at request time keeps the app
 * correct for any adopter overlay, and the short TTL bounds filesystem cost
 * without risking stale lists between edits.
 */
export function getIndex(repoRoot: string): Artifact[] {
  const now = Date.now();
  if (cache && now - cache.builtAt < CACHE_TTL_MS) {
    return cache.index;
  }
  const index = buildIndex(repoRoot);
  cache = { index, builtAt: now };
  return index;
}

/** Crawl the repo and build the full artifact index (uncached). */
export function buildIndex(repoRoot: string): Artifact[] {
  const items: Artifact[] = [];

  // The three artifact-bearing roots. external/* are per-suite subdirs.
  const ownRoots = ['synapse', 'src'];
  const externalSuites = listDirs(path.join(repoRoot, 'external'));

  // Skills: a directory containing SKILL.md is one artifact.
  for (const base of [...ownRoots, ...externalSuites.map((s) => path.join('external', s))]) {
    collectSkillLike(repoRoot, path.join(base, 'skills'), 'SKILL.md', 'skill', items);
    collectSkillLike(repoRoot, path.join(base, 'tools'), 'TOOL.md', 'tool', items);
    collectFlatMd(repoRoot, path.join(base, 'agents'), 'agent', items);
    collectFlatMd(repoRoot, path.join(base, 'protocols'), 'protocol', items);
  }

  // Pathways: top-level YAML files only.
  collectPathways(repoRoot, items);

  return items;
}

function collectSkillLike(
  repoRoot: string,
  relRoot: string,
  manifest: string,
  cls: ArtifactClass,
  out: Artifact[],
): void {
  const absRoot = path.join(repoRoot, relRoot);
  for (const file of walk(absRoot)) {
    if (path.basename(file) !== manifest) continue;
    const dir = path.dirname(file);
    const relPath = toRel(repoRoot, file);
    const { data } = parseFrontmatter(read(file));
    const slug = str(data.name) ?? path.basename(dir);
    const evalSibling = fs.existsSync(path.join(dir, 'EVAL.md'));
    out.push(makeArtifact(slug, cls, relPath, data, evalSibling));
  }
}

function collectFlatMd(
  repoRoot: string,
  relRoot: string,
  cls: ArtifactClass,
  out: Artifact[],
): void {
  const absRoot = path.join(repoRoot, relRoot);
  for (const file of walk(absRoot)) {
    const base = path.basename(file);
    if (!base.endsWith('.md')) continue;
    if (base === 'README.md' || base.endsWith('.eval.md')) continue;
    const relPath = toRel(repoRoot, file);
    // change_requests/ holds memos (FR5), not artifacts — exclude anywhere on
    // the path. The spec calls this out for protocols; the same CR dirs also
    // appear beside agents, and they are never agent definitions either.
    if (relPath.includes('/change_requests/')) continue;

    const { data } = parseFrontmatter(read(file));
    const slug = str(data.name) ?? base.replace(/\.md$/, '');
    const evalPath = file.replace(/\.md$/, '.eval.md');
    const hasEval = fs.existsSync(evalPath);
    out.push(makeArtifact(slug, cls, relPath, data, hasEval));
  }
}

function collectPathways(repoRoot: string, out: Artifact[]): void {
  const dir = path.join(repoRoot, 'pathways');
  let entries: fs.Dirent[];
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const e of entries) {
    if (!e.isFile() || !e.name.endsWith('.yaml')) continue;
    const file = path.join(dir, e.name);
    const { data } = parseFrontmatter(read(file));
    const slug = str(data.name) ?? e.name.replace(/\.yaml$/, '');
    out.push(makeArtifact(slug, 'pathway', toRel(repoRoot, file), data, false));
  }
}

function makeArtifact(
  slug: string,
  cls: ArtifactClass,
  relPath: string,
  data: Record<string, unknown>,
  hasEval: boolean,
): Artifact {
  return {
    slug,
    class: cls,
    layer: layerOf(relPath),
    path: relPath,
    domain: str(data.domain),
    status: str(data.status) ?? 'unknown',
    description: str(data.description),
    frontmatter: data,
    hasEval,
  };
}

function layerOf(relPath: string): Layer {
  if (relPath.startsWith('synapse/')) return 'base';
  if (relPath.startsWith('src/')) return 'addon';
  return 'external';
}

// --- registry-row matching ------------------------------------------------

/**
 * Find the markdown-table row whose first-column slug matches `slug`. Registry
 * tables render the slug as a `[slug](path)` link in column one; we strip the
 * link to compare. Returns a header->cell map, or null when absent.
 */
export function matchRegistryRow(tableText: string, slug: string): Record<string, string> | null {
  const lines = tableText.split(/\r?\n/).filter((l) => l.trim().startsWith('|'));
  if (lines.length < 2) return null;

  const headers = splitRow(lines[0] ?? '');
  // lines[1] is the `|---|---|` separator; data rows follow.
  for (const line of lines.slice(2)) {
    const cells = splitRow(line);
    if (cells.length === 0) continue;
    const firstSlug = linkSlug(cells[0] ?? '');
    if (firstSlug === slug) {
      const row: Record<string, string> = {};
      headers.forEach((h, i) => {
        row[h] = cells[i] ?? '';
      });
      return row;
    }
  }
  return null;
}

function splitRow(line: string): string[] {
  const trimmed = line.trim().replace(/^\|/, '').replace(/\|$/, '');
  return trimmed.split('|').map((c) => c.trim());
}

function linkSlug(cell: string): string {
  const m = /\[([^\]]+)\]\([^)]*\)/.exec(cell);
  return (m?.[1] ?? cell).trim();
}

// --- pathway resolution ----------------------------------------------------

interface PathwayDoc {
  name?: unknown;
  inherits?: unknown;
  synapses?: unknown;
}

/**
 * Resolve a pathway by name, flattening any `inherits:` chain. Child synapse
 * lists win and are merged with (de-duplicated against) inherited parents, so a
 * pathway can extend a base bundle without restating it (FR1.4).
 */
export function resolvePathway(repoRoot: string, name: string): ResolvedPathway | null {
  const file = path.join(repoRoot, 'pathways', `${name}.yaml`);
  if (!fs.existsSync(file)) return null;
  return resolvePathwayFile(repoRoot, file, new Set());
}

function resolvePathwayFile(
  repoRoot: string,
  file: string,
  seen: Set<string>,
): ResolvedPathway | null {
  if (seen.has(file)) return null; // guard against inherit cycles
  seen.add(file);

  const { body, data } = parseFrontmatter(read(file));
  // synapses: live in the body (post-frontmatter YAML) per pathway format.
  let doc: PathwayDoc = {};
  try {
    const parsed = parseYaml(body);
    if (parsed !== null && typeof parsed === 'object') doc = parsed as PathwayDoc;
  } catch {
    doc = {};
  }

  const name = str(data.name) ?? path.basename(file).replace(/\.yaml$/, '');

  const result: ResolvedPathway = { name, skills: [], agents: [], protocols: [], tools: [] };

  // Merge parents first so the child can override / extend.
  for (const parent of asArray(doc.inherits)) {
    const pName = String(parent);
    const pFile = path.join(repoRoot, 'pathways', `${pName}.yaml`);
    const resolved = resolvePathwayFile(repoRoot, pFile, seen);
    if (resolved) mergeSynapses(result, resolved);
  }

  const syn = (doc.synapses ?? {}) as Record<string, unknown>;
  mergeSynapses(result, {
    name,
    skills: asArray(syn.skills).map(String),
    agents: asArray(syn.agents).map(String),
    protocols: asArray(syn.protocols).map(String),
    tools: asArray(syn.tools).map(String),
  });

  return result;
}

function mergeSynapses(target: ResolvedPathway, src: ResolvedPathway): void {
  for (const key of ['skills', 'agents', 'protocols', 'tools'] as const) {
    const merged = new Set([...target[key], ...src[key]]);
    target[key] = [...merged];
  }
}

// --- low-level fs helpers --------------------------------------------------

/** Recursively yield every file under `dir`, skipping SKIP_DIRS. */
function* walk(dir: string): Generator<string> {
  let entries: fs.Dirent[];
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const e of entries) {
    if (e.isDirectory()) {
      if (SKIP_DIRS.has(e.name)) continue;
      yield* walk(path.join(dir, e.name));
    } else if (e.isFile()) {
      yield path.join(dir, e.name);
    }
  }
}

function listDirs(dir: string): string[] {
  try {
    return fs
      .readdirSync(dir, { withFileTypes: true })
      .filter((e) => e.isDirectory() && !SKIP_DIRS.has(e.name))
      .map((e) => e.name);
  } catch {
    return [];
  }
}

function read(file: string): string {
  try {
    return fs.readFileSync(file, 'utf8');
  } catch {
    return '';
  }
}

function toRel(repoRoot: string, file: string): string {
  return path.relative(repoRoot, file).split(path.sep).join('/');
}

function asArray(v: unknown): unknown[] {
  return Array.isArray(v) ? v : [];
}

function str(v: unknown): string | null {
  return typeof v === 'string' ? v : null;
}
