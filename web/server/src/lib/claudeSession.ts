// Headless claude driver (FR6 / DESIGN.md decision #2): the ONE module that
// spawns `claude -p --output-format stream-json --verbose`, parses its JSONL
// stdout line-by-line, and re-emits typed events. Reused by brainstorm chat
// (FR6) and creator runs (FR7). Tests inject a fake binary via CLAUDE_BIN.
//
// SAFETY (NFR5): the binary is always spawned with an ARG ARRAY (no shell), so
// the user prompt can never be shell-interpolated. The child is tracked in a
// module-level registry and killed on abort/disconnect; on exit we always flush
// the meta status so we never leave a session marked `running` forever.
import { type ChildProcessWithoutNullStreams, spawn } from 'node:child_process';
import { EventEmitter } from 'node:events';
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import { randomUUID } from 'node:crypto';
import type { SessionEvent, SessionEventType, SessionMeta } from '../../../shared/types';

/** The claude binary to spawn. Real `claude` in prod; a fake script in tests. */
function claudeBin(): string {
  const env = process.env.CLAUDE_BIN;
  return env !== undefined && env !== '' ? env : 'claude';
}

/** A live, in-memory session: its child, event bus, and current meta. */
export interface ActiveSession {
  id: string;
  child: ChildProcessWithoutNullStreams;
  emitter: EventEmitter;
  meta: SessionMeta;
  /** Resolves the claude session id, filled once init/result provides it. */
  claudeSessionId: string | null;
  /** The directory this session's transcript + meta live in. */
  sessionDir: string;
}

/** Module-level registry of active sessions so the SSE route can attach. */
const registry = new Map<string, ActiveSession>();

/** Default session store: `<repoRoot>/web/.sessions` (gitignored). */
export function defaultSessionDir(repoRoot: string): string {
  return path.join(repoRoot, 'web', '.sessions');
}

function ensureDir(dir: string): void {
  fs.mkdirSync(dir, { recursive: true });
}

function metaPath(sessionDir: string, id: string): string {
  return path.join(sessionDir, `${id}.meta.json`);
}

function jsonlPath(sessionDir: string, id: string): string {
  return path.join(sessionDir, `${id}.jsonl`);
}

function writeMeta(sessionDir: string, meta: SessionMeta): void {
  ensureDir(sessionDir);
  const tmp = path.join(sessionDir, `.${meta.id}.meta.${process.pid}.tmp`);
  fs.writeFileSync(tmp, JSON.stringify(meta, null, 2), 'utf8');
  fs.renameSync(tmp, metaPath(sessionDir, meta.id));
}

/** Read one persisted meta file, or null when missing/corrupt. */
export function readMeta(sessionDir: string, id: string): SessionMeta | null {
  try {
    const raw = fs.readFileSync(metaPath(sessionDir, id), 'utf8');
    return JSON.parse(raw) as SessionMeta;
  } catch {
    return null;
  }
}

/** List persisted sessions, newest first (FR6.3). */
export function listSessions(sessionDir: string): SessionMeta[] {
  let names: string[];
  try {
    names = fs.readdirSync(sessionDir);
  } catch {
    return [];
  }
  const metas: SessionMeta[] = [];
  for (const name of names) {
    if (!name.endsWith('.meta.json')) continue;
    const id = name.slice(0, -'.meta.json'.length);
    const meta = readMeta(sessionDir, id);
    if (meta) metas.push(meta);
  }
  return metas.sort((a, b) => b.startedAt.localeCompare(a.startedAt));
}

/** Parse a persisted transcript into typed events for reload (FR6.4). */
export function readTranscript(sessionDir: string, id: string): SessionEvent[] {
  let raw: string;
  try {
    raw = fs.readFileSync(jsonlPath(sessionDir, id), 'utf8');
  } catch {
    return [];
  }
  const events: SessionEvent[] = [];
  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    try {
      const obj = JSON.parse(trimmed) as { type?: string };
      events.push({ type: classify(obj.type), data: obj });
    } catch {
      // A non-JSON line in the transcript (shouldn't happen) — skip it.
    }
  }
  return events;
}

/** Map a stream-json `type` field to our event taxonomy. */
function classify(type: string | undefined): SessionEventType {
  switch (type) {
    case 'system':
      return 'system';
    case 'assistant':
      return 'assistant';
    case 'user':
      return 'user';
    case 'result':
      return 'result';
    default:
      // Unknown line types ride the assistant channel so nothing is dropped.
      return 'assistant';
  }
}

/** Pull a claude session id out of a system/result line, if present. */
function extractSessionId(obj: Record<string, unknown>): string | null {
  const sid = obj['session_id'];
  return typeof sid === 'string' && sid !== '' ? sid : null;
}

/** A short title from the user's first message (strip skill prefix, clamp). */
function deriveTitle(prompt: string): string {
  const stripped = prompt.replace(/^\/\S+\s*/, '').trim() || prompt.trim();
  const firstLine = stripped.split('\n')[0] ?? stripped;
  return firstLine.length > 60 ? `${firstLine.slice(0, 57)}…` : firstLine || 'session';
}

interface SpawnArgs {
  repoRoot: string;
  prompt: string;
  sessionDir?: string;
  /** When set, an existing session id to drive (kept stable across resume). */
  id?: string;
  /** When set, adds `--resume <claudeSessionId>` (resume path). */
  resumeClaudeSessionId?: string;
  /** Title override (resume keeps the original session's title). */
  title?: string;
}

/**
 * Core spawn used by both startSession and resumeSession. Builds the arg array,
 * spawns with cwd=repoRoot (no shell), wires stdout/stderr parsing, persists the
 * transcript + meta, and registers the session. The returned object exposes the
 * emitter so a caller (the SSE route) can attach live.
 */
function spawnClaude(args: SpawnArgs): ActiveSession {
  const sessionDir = args.sessionDir ?? defaultSessionDir(args.repoRoot);
  ensureDir(sessionDir);
  const id = args.id ?? randomUUID();

  const argv = ['-p', args.prompt, '--output-format', 'stream-json', '--verbose'];
  if (args.resumeClaudeSessionId) {
    argv.push('--resume', args.resumeClaudeSessionId);
  }

  const child = spawn(claudeBin(), argv, {
    cwd: args.repoRoot,
    // Explicitly no shell — the prompt is a single argv element, never parsed.
    shell: false,
  }) as ChildProcessWithoutNullStreams;

  const emitter = new EventEmitter();
  // The SSE route can attach many listeners (replay + live); lift the cap.
  emitter.setMaxListeners(0);

  const existing = args.id ? readMeta(sessionDir, args.id) : null;
  const meta: SessionMeta = {
    id,
    claudeSessionId: args.resumeClaudeSessionId ?? existing?.claudeSessionId ?? null,
    status: 'running',
    startedAt: existing?.startedAt ?? new Date().toISOString(),
    prompt: args.prompt,
    title: args.title ?? existing?.title ?? deriveTitle(args.prompt),
  };
  writeMeta(sessionDir, meta);

  const session: ActiveSession = {
    id,
    child,
    emitter,
    meta,
    claudeSessionId: meta.claudeSessionId,
    sessionDir,
  };
  registry.set(id, session);

  // Append every raw JSONL line to the transcript as it arrives. Open in append
  // mode so a resume adds to the same transcript without clobbering it.
  const out = fs.createWriteStream(jsonlPath(sessionDir, id), { flags: 'a' });

  const rl = readline.createInterface({ input: child.stdout });
  rl.on('line', (line) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    out.write(`${trimmed}\n`);
    let obj: Record<string, unknown>;
    try {
      obj = JSON.parse(trimmed) as Record<string, unknown>;
    } catch {
      emitter.emit('event', { type: 'error', data: { message: 'unparseable line', line: trimmed } });
      return;
    }
    const type = classify(typeof obj['type'] === 'string' ? (obj['type'] as string) : undefined);
    // Capture the claude session id from system (init) or result lines.
    const sid = extractSessionId(obj);
    if (sid && session.claudeSessionId !== sid) {
      session.claudeSessionId = sid;
      meta.claudeSessionId = sid;
      writeMeta(sessionDir, meta);
    }
    const event: SessionEvent = { type, data: obj };
    emitter.emit('event', event);
  });

  child.stderr.on('data', (chunk: Buffer) => {
    emitter.emit('event', { type: 'stderr', data: { text: chunk.toString('utf8') } });
  });

  child.on('error', (err) => {
    meta.status = 'error';
    writeMeta(sessionDir, meta);
    emitter.emit('event', { type: 'error', data: { message: err.message } });
  });

  child.on('exit', (code, signal) => {
    rl.close();
    out.end();
    // Don't downgrade an explicit kill/error: only mark done on a clean exit.
    if (meta.status === 'running') {
      meta.status = code === 0 ? 'done' : 'error';
      writeMeta(sessionDir, meta);
    }
    const event: SessionEvent = {
      type: 'exit',
      data: { code, signal, status: meta.status },
    };
    emitter.emit('event', event);
    registry.delete(id);
  });

  return session;
}

/** Start a fresh headless claude session (FR6.1). */
export function startSession(args: {
  repoRoot: string;
  prompt: string;
  sessionDir?: string;
  title?: string;
}): ActiveSession {
  return spawnClaude(args);
}

/**
 * Resume a session by claude session id with a new message (FR6.2). Reuses our
 * own session id so the transcript/meta accumulate in one place across turns.
 */
export function resumeSession(args: {
  repoRoot: string;
  prompt: string;
  claudeSessionId: string;
  id: string;
  sessionDir?: string;
}): ActiveSession {
  return spawnClaude({
    repoRoot: args.repoRoot,
    prompt: args.prompt,
    sessionDir: args.sessionDir,
    id: args.id,
    resumeClaudeSessionId: args.claudeSessionId,
  });
}

/** The live session for an id, if one is currently running. */
export function getActiveSession(id: string): ActiveSession | undefined {
  return registry.get(id);
}

/**
 * Kill a session's child process (SIGTERM) and mark its meta `error` (an abort
 * is not a clean completion). Idempotent: returns false when nothing was live.
 * Persists the status immediately so an aborted session reflects right away,
 * even before the child's exit handler fires.
 */
export function killSession(id: string): boolean {
  const session = registry.get(id);
  if (!session) return false;
  session.meta.status = 'error';
  try {
    writeMeta(session.sessionDir, session.meta);
  } catch {
    /* best effort — the exit handler will also persist */
  }
  session.child.kill('SIGTERM');
  session.emitter.emit('event', { type: 'error', data: { message: 'aborted' } });
  return true;
}
