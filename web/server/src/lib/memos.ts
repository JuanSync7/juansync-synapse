// Memo crawl + byte-preserving executed-flag PATCH (FR5, DESIGN.md decision #3).
//
// A memo is an actionable artifact-creation record. Two sources feed the board:
//   (a) brainstorm `.brainstorms/<slug>/meta.yaml` `artifacts[]` entries, each
//       joined to its `memo_path` file when that file exists;
//   (b) standalone `**/change_requests/*.md` files not already referenced by a
//       meta.yaml entry.
// The artifact crawler skips `.brainstorms/` (it is not a synapse artifact tree),
// so this module owns its own crawl with a memo-specific skip set.
//
// `executed` resolution, in priority order (FR5.1):
//   1. memo file YAML frontmatter `executed:`  → executedSource 'frontmatter'
//   2. else meta.yaml artifact status terminal? → executedSource 'meta'
//   3. else                                     → executedSource 'default' (false)
//
// setMemoExecuted rewrites ONLY the frontmatter region, preserving the body
// byte-for-byte, and routes the actual write through safeWrite for the atomic +
// containment guarantees. The write is allowed only for memo paths (a
// `change_requests/` segment, or under `.brainstorms/`) — enforced by isMemoPath
// AND by safeWrite's allow-list, so a crafted id can never escape to arbitrary
// repo files.
import fs from 'node:fs';
import path from 'node:path';
import { parse as parseYaml } from 'yaml';
import type { Memo, MemoExecutedSource } from '../../../shared/types';
import { parseFrontmatter } from './frontmatter';
import { safeWrite } from './safeWrite';

// Never descend into these (mirrors crawler.SKIP_DIRS, but KEEPS .brainstorms
// because that is where brainstorm memos live).
const SKIP_DIRS = new Set(['node_modules', '.git', 'web', 'dist', '.delivery']);

// meta.yaml artifact statuses that mean the artifact was actually created/applied.
const TERMINAL_META_STATUSES = new Set(['done', 'applied', 'created', 'executed', 'merged']);

interface MetaArtifact {
  name?: unknown;
  type?: unknown;
  status?: unknown;
  memo_path?: unknown;
}

/** A brainstorm meta.yaml row indexed by its resolved memo file path (when any). */
interface MetaEntry {
  slug: string;
  name: string;
  type: string | null;
  status: string | null;
  /** Repo-relative POSIX memo_path, or null when absent in the meta. */
  memoPath: string | null;
}

/** True when `relPath` is a writable memo location (FR5.2 / NFR5 allow-list). */
export function isMemoPath(relPath: string): boolean {
  const norm = relPath.split(path.sep).join('/');
  return norm.includes('change_requests/') || norm.startsWith('.brainstorms/');
}

/**
 * Crawl the repo for memos. Brainstorm meta.yaml entries come first (joined to
 * their memo files when present); standalone change_requests memos that no
 * meta.yaml already claims come second. Never throws on a bad file — a malformed
 * meta.yaml or memo yields a best-effort record rather than 500-ing the board.
 */
export function crawlMemos(repoRoot: string): Memo[] {
  const metaEntries = collectMetaEntries(repoRoot);
  // Index meta entries by the file they reference, so a standalone-CR scan can
  // tell which change_requests files are already owned by a brainstorm session.
  const byPath = new Map<string, MetaEntry>();
  for (const e of metaEntries) {
    if (e.memoPath) byPath.set(e.memoPath, e);
  }

  const memos: Memo[] = [];
  const seenPaths = new Set<string>();

  // (a) brainstorm memos — one per meta.yaml artifacts[] entry.
  for (const e of metaEntries) {
    const absPath = e.memoPath ? path.join(repoRoot, e.memoPath) : null;
    const fileExists = absPath !== null && fs.existsSync(absPath);
    const raw = fileExists ? read(absPath) : '';
    const fmExecuted = fileExists ? frontmatterExecuted(raw) : null;

    let executed: boolean;
    let executedSource: MemoExecutedSource;
    if (fmExecuted !== null) {
      executed = fmExecuted;
      executedSource = 'frontmatter';
    } else if (e.status !== null) {
      executed = TERMINAL_META_STATUSES.has(e.status.toLowerCase());
      executedSource = 'meta';
    } else {
      executed = false;
      executedSource = 'default';
    }

    const relPath = e.memoPath && fileExists ? e.memoPath : null;
    if (relPath) seenPaths.add(relPath);

    memos.push({
      // id is path-derived when a file exists; otherwise derive a stable
      // pseudo-id from the session slug + artifact name so the row is addressable.
      id: relPath ? idFromPath(relPath) : idFromPath(`.brainstorms/${e.slug}/${e.name}`),
      title: fileExists ? firstHeading(raw) ?? e.name : e.name,
      source: `brainstorm:${e.slug}`,
      session: e.slug,
      artifactType: e.type,
      executed,
      executedSource,
      path: relPath,
      createdDate: dateFromName(relPath ? path.basename(relPath) : ''),
    });
  }

  // (b) standalone change_requests memos not claimed by any meta.yaml.
  for (const file of walk(repoRoot)) {
    const relPath = toRel(repoRoot, file);
    if (!relPath.includes('/change_requests/') && !relPath.startsWith('change_requests/')) continue;
    const base = path.basename(file);
    if (base === 'README.md' || !base.endsWith('.md')) continue;
    if (seenPaths.has(relPath) || byPath.has(relPath)) continue;
    seenPaths.add(relPath);

    const raw = read(file);
    const fmExecuted = frontmatterExecuted(raw);
    const executed = fmExecuted ?? false;
    const executedSource: MemoExecutedSource = fmExecuted !== null ? 'frontmatter' : 'default';

    memos.push({
      id: idFromPath(relPath),
      title: firstHeading(raw) ?? base.replace(/\.md$/, ''),
      source: `change_requests:${path.dirname(relPath)}`,
      session: null,
      artifactType: inferType(relPath),
      executed,
      executedSource,
      path: relPath,
      createdDate: dateFromName(base),
    });
  }

  return memos;
}

/**
 * Set a memo's `executed` frontmatter flag, preserving the body byte-for-byte.
 * Resolves the id → path via crawlMemos (never interpolates the id into a path),
 * then writes through safeWrite with the memo allow-list. Throws when the id is
 * unknown or the memo has no backing file yet (a not-yet-created brainstorm memo
 * cannot be toggled).
 */
export function setMemoExecuted(repoRoot: string, id: string, executed: boolean): Memo {
  const memo = crawlMemos(repoRoot).find((m) => m.id === id);
  if (!memo) {
    throw new Error(`Unknown memo id: ${id}`);
  }
  if (!memo.path) {
    throw new Error(`Memo ${id} has no backing file to update.`);
  }
  if (!isMemoPath(memo.path)) {
    // Defense in depth: crawlMemos only yields memo paths, but never trust it.
    throw new Error(`Refusing to write a non-memo path: ${memo.path}`);
  }

  const abs = path.join(repoRoot, memo.path);
  const original = read(abs);
  const next = rewriteExecuted(original, executed);

  // The allow-list is `.brainstorms` plus the change_requests dir of this memo.
  // safeWrite gives the atomic-write + symlink-containment guarantees; the dir
  // list keeps the blast radius to exactly this memo's neighbourhood.
  const allowDirs = ['.brainstorms', path.dirname(memo.path)];
  safeWrite(repoRoot, memo.path, next, allowDirs);

  return {
    ...memo,
    executed,
    executedSource: 'frontmatter',
  };
}

/**
 * Return the file content with its frontmatter `executed:` set to `value`.
 * If the file already has a `---` block, only that block is rewritten (the body
 * after it is untouched). If it has none, a minimal block is prepended and the
 * entire original content follows byte-for-byte.
 */
function rewriteExecuted(original: string, value: boolean): string {
  const { data, body } = parseFrontmatter(original);
  const hasFrontmatter = original.startsWith('---');

  if (!hasFrontmatter || Object.keys(data).length === 0) {
    // No (or unparseable) frontmatter → prepend a minimal block, keep the rest.
    // We treat an empty parse as "no block" to avoid mangling a malformed head.
    if (!hasFrontmatter) {
      return `---\nexecuted: ${value}\n---\n${original}`;
    }
  }

  // Rewrite only the frontmatter region: re-extract its exact text so the body
  // (everything after the closing fence) is preserved verbatim.
  const fenceMatch = /^---[ \t]*\r?\n([\s\S]*?)\r?\n---[ \t]*\r?\n?/.exec(original);
  if (!fenceMatch) {
    return `---\nexecuted: ${value}\n---\n${original}`;
  }
  const yamlText = fenceMatch[1] ?? '';
  const lines = yamlText.split(/\r?\n/);
  let found = false;
  const newLines = lines.map((line) => {
    if (/^executed\s*:/.test(line)) {
      found = true;
      return `executed: ${value}`;
    }
    return line;
  });
  if (!found) newLines.push(`executed: ${value}`);

  const newFront = `---\n${newLines.join('\n')}\n---\n`;
  return newFront + body;
}

// --- meta.yaml collection --------------------------------------------------

function collectMetaEntries(repoRoot: string): MetaEntry[] {
  const out: MetaEntry[] = [];
  const brainstormsDir = path.join(repoRoot, '.brainstorms');
  let sessions: fs.Dirent[];
  try {
    sessions = fs.readdirSync(brainstormsDir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const s of sessions) {
    if (!s.isDirectory()) continue;
    const metaFile = path.join(brainstormsDir, s.name, 'meta.yaml');
    if (!fs.existsSync(metaFile)) continue;
    let doc: { slug?: unknown; artifacts?: unknown };
    try {
      const parsed = parseYaml(read(metaFile));
      doc = parsed !== null && typeof parsed === 'object' ? (parsed as typeof doc) : {};
    } catch {
      doc = {};
    }
    const slug = str(doc.slug) ?? s.name;
    const artifacts = Array.isArray(doc.artifacts) ? (doc.artifacts as MetaArtifact[]) : [];
    for (const a of artifacts) {
      const name = str(a.name);
      if (!name) continue;
      out.push({
        slug,
        name,
        type: str(a.type),
        status: str(a.status),
        memoPath: str(a.memo_path),
      });
    }
  }
  return out;
}

// --- helpers ---------------------------------------------------------------

/** Parse the frontmatter `executed:` flag → boolean, or null when absent. */
function frontmatterExecuted(raw: string): boolean | null {
  const { data } = parseFrontmatter(raw);
  const v = data.executed;
  if (typeof v === 'boolean') return v;
  if (typeof v === 'string') {
    const low = v.trim().toLowerCase();
    if (low === 'true') return true;
    if (low === 'false') return false;
  }
  return null;
}

/** Path-derived id: `/`→`__`, `.md` stripped, url-safe. */
function idFromPath(relPath: string): string {
  return relPath.replace(/\.md$/, '').split('/').join('__');
}

/** First `# ` heading text, or null. */
function firstHeading(raw: string): string | null {
  for (const line of raw.split(/\r?\n/)) {
    const m = /^#\s+(.+?)\s*$/.exec(line);
    if (m) return m[1] ?? null;
  }
  return null;
}

/** Leading YYYY-MM-DD from a filename, else null. */
function dateFromName(name: string): string | null {
  const m = /^(\d{4}-\d{2}-\d{2})/.exec(name);
  return m ? (m[1] ?? null) : null;
}

/** Infer an artifact type from the path (protocols→protocol, skills→skill, …). */
function inferType(relPath: string): string | null {
  if (relPath.includes('/protocols/') || relPath.startsWith('protocols/')) return 'protocol';
  if (relPath.includes('/skills/') || relPath.startsWith('skills/')) return 'skill';
  if (relPath.includes('/agents/') || relPath.startsWith('agents/')) return 'agent';
  if (relPath.includes('/tools/') || relPath.startsWith('tools/')) return 'tool';
  if (relPath.includes('/pathways/') || relPath.startsWith('pathways/')) return 'pathway';
  return null;
}

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

function str(v: unknown): string | null {
  return typeof v === 'string' ? v : null;
}
