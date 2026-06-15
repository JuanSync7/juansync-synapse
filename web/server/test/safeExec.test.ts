import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { isAllowed, runAllowed } from '../src/lib/safeExec';

describe('isAllowed (allow-list gate)', () => {
  it('allows the read-only cortex invocations', () => {
    expect(isAllowed('./cortex', ['validate'])).toBe(true);
    expect(isAllowed('cortex', ['list'])).toBe(true);
    expect(isAllowed('./cortex', ['available'])).toBe(true);
    expect(isAllowed('./cortex', ['doctor'])).toBe(true);
    expect(isAllowed('./cortex', ['pin', 'status'])).toBe(true);
    expect(isAllowed('./cortex', ['pathway', 'list'])).toBe(true);
  });

  it('rejects destructive / unknown subcommands', () => {
    expect(isAllowed('./cortex', ['clean'])).toBe(false);
    expect(isAllowed('./cortex', ['rm'])).toBe(false);
    expect(isAllowed('./cortex', ['pin', 'add'])).toBe(false);
    expect(isAllowed('./cortex', ['pathway', 'install'])).toBe(false);
    expect(isAllowed('./cortex', [])).toBe(false);
  });

  it('rejects any command other than cortex', () => {
    expect(isAllowed('rm', ['-rf', '/'])).toBe(false);
    expect(isAllowed('bash', ['-c', 'validate'])).toBe(false);
    expect(isAllowed('git', ['status'])).toBe(false);
  });

  it('treats shell-injection-shaped args as a single non-matching token', () => {
    // execFile takes the arg array literally; '; rm -rf' is one opaque token,
    // not a shell sequence, and it is not in the allow-list → rejected.
    expect(isAllowed('./cortex', ['; rm -rf'])).toBe(false);
    expect(isAllowed('./cortex', ['validate; rm -rf /'])).toBe(false);
  });
});

describe('runAllowed', () => {
  let root: string;

  beforeEach(() => {
    root = fs.mkdtempSync(path.join(os.tmpdir(), 'safe-exec-'));
    // A fake cortex that echoes its args, proving execFile passes them literally
    // (no shell expansion) and that cwd is the repo root.
    const fake = [
      '#!/usr/bin/env bash',
      'echo "ARGS:$*"',
      'echo "CWD:$(pwd)"',
      'exit 0',
    ].join('\n');
    fs.writeFileSync(path.join(root, 'cortex'), fake, { mode: 0o755 });
  });

  afterEach(() => fs.rmSync(root, { recursive: true, force: true }));

  it('throws for a non-allow-listed command without executing', async () => {
    await expect(runAllowed(root, './cortex', ['clean'])).rejects.toThrow(/not allowed/i);
  });

  it('runs an allow-listed command via execFile (no shell) and captures output', async () => {
    const res = await runAllowed(root, './cortex', ['list']);
    expect(res.exitCode).toBe(0);
    expect(res.stdout).toContain('ARGS:list');
    expect(res.command).toContain('cortex');
  });

  it('does not shell-expand a malicious-looking arg (allow-list rejects it first)', async () => {
    await expect(runAllowed(root, './cortex', ['validate; rm -rf /'])).rejects.toThrow(
      /not allowed/i,
    );
    // The temp repo is untouched: cortex file still present.
    expect(fs.existsSync(path.join(root, 'cortex'))).toBe(true);
  });
});
