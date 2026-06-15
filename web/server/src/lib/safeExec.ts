import { execFile } from 'node:child_process';
import path from 'node:path';
import type { ExecResult } from '../../../shared/types';

// The complete allow-list (FR8.3, NFR5). Read-only cortex invocations only.
// Single-token subcommands and a small set of explicit two-token ones. Anything
// not matched here is refused before any process is spawned. This list is the
// security boundary — never widen it to include write/destructive subcommands
// (clean, sync, scaffold, install, drift restore, …).
const SINGLE_TOKEN = new Set(['validate', 'list', 'available', 'doctor']);
const TWO_TOKEN = new Set(['pin status', 'pathway list']);

// Only the repo's own cortex dispatcher may be the command — by relative path
// (resolved against cwd=repoRoot) or bare name. No arbitrary binaries.
const ALLOWED_COMMANDS = new Set(['./cortex', 'cortex']);

const TIMEOUT_MS = 60_000;

/**
 * Pure allow-list predicate, exported for unit testing. Decides whether a
 * (command, args) pair is a permitted read-only cortex invocation. Because
 * matching is on exact tokens, a shell-injection-shaped argument like
 * `'validate; rm -rf /'` is a single opaque token that is not in the set, so it
 * is rejected — and even if it weren't, execFile never invokes a shell.
 */
export function isAllowed(command: string, args: string[]): boolean {
  if (!ALLOWED_COMMANDS.has(command)) return false;
  if (args.length === 0) return false;
  if (args.length === 1) return SINGLE_TOKEN.has(args[0] ?? '');
  if (args.length === 2) return TWO_TOKEN.has(`${args[0]} ${args[1]}`);
  return false;
}

/**
 * Run an allow-listed read-only cortex command and capture its output. Uses
 * execFile with an argument array (NO shell) so user-supplied args can never be
 * interpolated into a command line. cwd is pinned to the repo root, with a hard
 * 60s timeout. Throws synchronously-shaped (rejected promise) when the command
 * is not allow-listed; otherwise resolves with stdout/stderr/exitCode even when
 * the command exits non-zero (a failing validate is data, not an error).
 */
export function runAllowed(repoRoot: string, command: string, args: string[]): Promise<ExecResult> {
  if (!isAllowed(command, args)) {
    return Promise.reject(new Error(`Command not allowed: ${command} ${args.join(' ')}`.trim()));
  }

  // Resolve a relative './cortex' against the repo root; keep a bare name as-is
  // (it will still be looked up relative to cwd by execFile).
  const file = command.startsWith('.') ? path.join(repoRoot, command) : command;
  const display = `${command} ${args.join(' ')}`.trim();

  return new Promise<ExecResult>((resolve) => {
    execFile(
      file,
      args,
      { cwd: repoRoot, timeout: TIMEOUT_MS, maxBuffer: 8 * 1024 * 1024 },
      (err, stdout, stderr) => {
        const code =
          err && typeof (err as { code?: unknown }).code === 'number'
            ? ((err as { code: number }).code as number)
            : err
              ? 1
              : 0;
        resolve({ command: display, stdout: stdout ?? '', stderr: stderr ?? '', exitCode: code });
      },
    );
  });
}
