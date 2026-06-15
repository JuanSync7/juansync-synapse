// Creator end-to-end run driver (FR7 / DESIGN.md decision #2). Builds ON TOP of
// the claudeSession driver: a "run" is a headless claude session tagged as a
// creator-run, plus a POST-RUN VERIFICATION step the brainstorm chat does not
// have — a git-porcelain diff (what did the run create?) and a `./cortex
// validate` (did the framework stay green?).
//
// Lifecycle:
//   1. startCreatorRun: resolve memoId → memo file path (404 when unknown),
//      capture the git porcelain BASELINE, compose the creator prompt, spawn a
//      session via the driver, and persist a RunMeta {status:'running'}.
//   2. When the underlying claude session exits, run verification:
//        a. `git status --porcelain` (execFile, NO shell) → diff against the
//           baseline so createdPaths reflects ONLY this run's changes.
//        b. runAllowed(repoRoot, './cortex', ['validate']) → ExecResult.
//        c. status = 'succeeded' iff claude exited cleanly AND validate exit 0,
//           else 'failed'. Persist createdPaths + validate into the run meta.
//      A 'verification' event is emitted on the run's emitter so the SSE route
//      can forward it as a terminal frame after the session's own exit frame.
//
// SAFETY (NFR5): git is spawned with an arg array (no shell); validate goes
// through the safeExec allow-list. The run store lives under
// sessionDir/runs/ (sessionDir defaults to web/.sessions, gitignored), so a run
// never writes outside its own meta files.
import { execFile } from 'node:child_process';
import { EventEmitter } from 'node:events';
import fs from 'node:fs';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import type {
  ArtifactClass,
  CreatedPath,
  RunMeta,
  RunVerification,
} from '../../../shared/types';
import { crawlMemos } from './memos';
import { runAllowed } from './safeExec';
import {
  defaultSessionDir,
  getActiveSession,
  killSession,
  readTranscript,
  startSession,
  type ActiveSession,
} from './claudeSession';

/** A live run: its underlying session, an emitter for verification, and meta. */
export interface ActiveRun {
  id: string;
  session: ActiveSession;
  emitter: EventEmitter;
  meta: RunMeta;
}

/** Module-level registry of live runs so the SSE route can attach. */
const registry = new Map<string, ActiveRun>();

/** Where run meta + nothing-else live: `<sessionDir>/runs`. */
export function runsDir(sessionDir: string): string {
  return path.join(sessionDir, 'runs');
}

function ensureDir(dir: string): void {
  fs.mkdirSync(dir, { recursive: true });
}

function runMetaPath(dir: string, id: string): string {
  return path.join(dir, `${id}.meta.json`);
}

function writeRunMeta(dir: string, meta: RunMeta): void {
  ensureDir(dir);
  const tmp = path.join(dir, `.${meta.id}.meta.${process.pid}.tmp`);
  fs.writeFileSync(tmp, JSON.stringify(meta, null, 2), 'utf8');
  fs.renameSync(tmp, runMetaPath(dir, meta.id));
}

/** Read one persisted run meta, or null when missing/corrupt. */
export function readRunMeta(dir: string, id: string): RunMeta | null {
  try {
    const raw = fs.readFileSync(runMetaPath(dir, id), 'utf8');
    return JSON.parse(raw) as RunMeta;
  } catch {
    return null;
  }
}

/** List persisted runs, newest first (FR7.3). */
export function listRuns(sessionDir: string): RunMeta[] {
  const dir = runsDir(sessionDir);
  let names: string[];
  try {
    names = fs.readdirSync(dir);
  } catch {
    return [];
  }
  const out: RunMeta[] = [];
  for (const name of names) {
    if (!name.endsWith('.meta.json')) continue;
    const id = name.slice(0, -'.meta.json'.length);
    const meta = readRunMeta(dir, id);
    if (meta) out.push(meta);
  }
  return out.sort((a, b) => b.startedAt.localeCompare(a.startedAt));
}

/** The persisted run meta for an id. */
export function getRun(sessionDir: string, id: string): RunMeta | null {
  return readRunMeta(runsDir(sessionDir), id);
}

/** The live run for an id, if one is currently running. */
export function getActiveRun(id: string): ActiveRun | undefined {
  return registry.get(id);
}

/** Compose the creator prompt instructing an end-to-end run against a memo. */
export function creatorPrompt(memoPath: string): string {
  return (
    `/synapse-router-artifact-creator ` +
    `Use the memo at \`${memoPath}\` as the artifact specification. ` +
    `Proceed end-to-end without pausing: scaffold the artifact, generate its ` +
    `EVAL.md, update the registry, and update the directory READMEs. ` +
    `Report the created artifact path when done.`
  );
}

/**
 * Capture `git status --porcelain` as a set of lines. execFile (no shell); cwd
 * pinned to repoRoot. Returns [] on any git error (a non-repo or git-less env
 * yields an empty baseline rather than crashing the run).
 */
function gitPorcelain(repoRoot: string): Promise<string[]> {
  return new Promise((resolve) => {
    execFile(
      'git',
      // -uall lists individual untracked FILES (not collapsed dirs) so a freshly
      // created artifact shows as its SKILL.md path, not just its directory.
      ['status', '--porcelain', '-uall'],
      { cwd: repoRoot, timeout: 30_000, maxBuffer: 8 * 1024 * 1024 },
      (err, stdout) => {
        if (err) {
          resolve([]);
          return;
        }
        const lines = stdout.split('\n').map((l) => l.replace(/\s+$/, '')).filter((l) => l !== '');
        resolve(lines);
      },
    );
  });
}

/** Parse a porcelain line `XY path` → { status, path } (POSIX path). */
function parsePorcelainLine(line: string): { status: string; path: string } | null {
  // Porcelain: 2 status chars, a space, then the path. Renames use `old -> new`.
  const m = /^(..)\s+(.+)$/.exec(line);
  if (!m) return null;
  const status = (m[1] ?? '').trim();
  let p = m[2] ?? '';
  const arrow = p.indexOf(' -> ');
  if (arrow !== -1) p = p.slice(arrow + 4);
  p = p.replace(/^"(.*)"$/, '$1');
  return { status, path: p.split(path.sep).join('/') };
}

/** Infer artifact {class, slug} from a defining-file path, else null. */
export function inferArtifact(relPath: string): { class: ArtifactClass; slug: string } | null {
  const base = path.basename(relPath);
  const defining: Record<string, ArtifactClass> = {
    'SKILL.md': 'skill',
    'AGENT.md': 'agent',
    'PROTOCOL.md': 'protocol',
    'TOOL.md': 'tool',
    'PATHWAY.md': 'pathway',
  };
  const cls = defining[base];
  if (!cls) return null;
  const slug = path.basename(path.dirname(relPath));
  if (!slug || slug === '.') return null;
  return { class: cls, slug };
}

/** Diff `after` against `before`, returning only the new/changed lines. */
function diffPorcelain(before: string[], after: string[]): CreatedPath[] {
  const baseline = new Set(before);
  const out: CreatedPath[] = [];
  for (const line of after) {
    if (baseline.has(line)) continue;
    const parsed = parsePorcelainLine(line);
    if (!parsed) continue;
    out.push({
      path: parsed.path,
      status: parsed.status,
      artifact: inferArtifact(parsed.path),
    });
  }
  return out;
}

/** Read the persisted verification (createdPaths + validate) for a run, or null. */
export function readVerification(sessionDir: string, id: string): RunVerification | null {
  const meta = getRun(sessionDir, id);
  if (!meta || !meta.createdPaths || !meta.validate) return null;
  return { createdPaths: meta.createdPaths, validate: meta.validate };
}

/** Read a run's underlying session transcript (delegates to the driver). */
export function readRunTranscript(sessionDir: string, id: string) {
  const meta = getRun(sessionDir, id);
  if (!meta) return [];
  return readTranscript(sessionDir, meta.sessionId);
}

/**
 * Run the post-session verification: git porcelain diff + validate, then update
 * the run meta with status + createdPaths + validate and emit a 'verification'
 * event. `claudeOk` is whether the claude session exited cleanly (status done).
 */
async function verify(
  run: ActiveRun,
  repoRoot: string,
  sessionDir: string,
  baseline: string[],
  claudeOk: boolean,
): Promise<void> {
  const after = await gitPorcelain(repoRoot);
  const createdPaths = diffPorcelain(baseline, after);

  let validate;
  try {
    validate = await runAllowed(repoRoot, './cortex', ['validate']);
  } catch {
    // runAllowed only rejects when the command is not allow-listed — it isn't
    // here, but be defensive: a missing validate counts as a failure signal.
    validate = { command: './cortex validate', stdout: '', stderr: 'validate unavailable', exitCode: 1 };
  }

  const dir = runsDir(sessionDir);
  run.meta.createdPaths = createdPaths;
  run.meta.validate = validate;
  run.meta.status = claudeOk && validate.exitCode === 0 ? 'succeeded' : 'failed';
  writeRunMeta(dir, run.meta);

  const verification: RunVerification = { createdPaths, validate };
  run.emitter.emit('verification', verification);
  registry.delete(run.id);
}

/**
 * Start a creator end-to-end run against a memo (FR7.1). Resolves memoId via
 * crawlMemos; throws a tagged error (`code:'NOT_FOUND'`) when the memo or its
 * file is unknown so the route can map it to a 404. Captures the git baseline
 * BEFORE spawning so createdPaths reflects only this run's changes.
 */
export function startCreatorRun(args: {
  repoRoot: string;
  memoId: string;
  sessionDir?: string;
}): Promise<ActiveRun> {
  const sessionDir = args.sessionDir ?? defaultSessionDir(args.repoRoot);
  const memo = crawlMemos(args.repoRoot).find((m) => m.id === args.memoId);
  if (!memo || !memo.path) {
    const err = new Error(`Unknown memo id: ${args.memoId}`) as Error & { code?: string };
    err.code = 'NOT_FOUND';
    return Promise.reject(err);
  }
  const memoPath = memo.path;

  // Capture the baseline BEFORE the run so the diff is run-scoped (NOTE in task).
  return gitPorcelain(args.repoRoot).then((baseline) => {
    const id = randomUUID();
    const prompt = creatorPrompt(memoPath);
    const session = startSession({
      repoRoot: args.repoRoot,
      prompt,
      sessionDir,
      title: `creator: ${memo.title}`,
    });

    const emitter = new EventEmitter();
    emitter.setMaxListeners(0);

    const meta: RunMeta = {
      id,
      kind: 'creator-run',
      memoId: args.memoId,
      memoPath,
      status: 'running',
      startedAt: new Date().toISOString(),
      sessionId: session.id,
    };
    writeRunMeta(runsDir(sessionDir), meta);

    const run: ActiveRun = { id, session, emitter, meta };
    registry.set(id, run);

    // Forward every session event to the run emitter so the SSE route streams
    // live progress; on the session's exit, kick off verification.
    session.emitter.on('event', (event: { type: string }) => {
      run.emitter.emit('session-event', event);
      if (event.type === 'exit') {
        const claudeOk = session.meta.status === 'done';
        void verify(run, args.repoRoot, sessionDir, baseline, claudeOk).catch(() => {
          // Verification should never throw (defensive), but if it does, mark
          // failed AND emit a verification frame so any attached SSE client gets
          // a terminal signal instead of hanging — then the run never sits
          // 'running' forever.
          const fallback: RunVerification = {
            createdPaths: [],
            validate: { command: './cortex validate', stdout: '', stderr: 'verification failed', exitCode: 1 },
          };
          run.meta.status = 'failed';
          run.meta.createdPaths = fallback.createdPaths;
          run.meta.validate = fallback.validate;
          writeRunMeta(runsDir(sessionDir), run.meta);
          run.emitter.emit('verification', fallback);
          registry.delete(run.id);
        });
      }
    });

    return run;
  });
}

/** Abort a run: kill its underlying claude session and mark the run failed. */
export function abortRun(sessionDir: string, id: string): boolean {
  const run = registry.get(id);
  const meta = run?.meta ?? getRun(sessionDir, id);
  if (!meta) return false;
  let killed = false;
  if (run) {
    killed = killSession(run.session.id);
    run.meta.status = 'failed';
    writeRunMeta(runsDir(sessionDir), run.meta);
  } else if (meta.status === 'running') {
    killed = killSession(meta.sessionId);
    meta.status = 'failed';
    writeRunMeta(runsDir(sessionDir), meta);
  }
  return killed;
}

/** True when a session id currently has a live process (helper for routes). */
export function sessionIsActive(sessionId: string): boolean {
  return getActiveSession(sessionId) !== undefined;
}
