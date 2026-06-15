import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { safeWrite, PathNotAllowedError } from '../src/lib/safeWrite';

let root: string;

beforeEach(() => {
  root = fs.mkdtempSync(path.join(os.tmpdir(), 'safewrite-'));
  fs.mkdirSync(path.join(root, 'registry'));
  fs.mkdirSync(path.join(root, 'taxonomy'));
  fs.mkdirSync(path.join(root, 'secret'));
});

afterEach(() => {
  fs.rmSync(root, { recursive: true, force: true });
});

describe('safeWrite', () => {
  it('writes a file inside an allow-listed dir', () => {
    safeWrite(root, 'registry/SKILL_REGISTRY.md', 'hello', ['registry']);
    expect(fs.readFileSync(path.join(root, 'registry/SKILL_REGISTRY.md'), 'utf8')).toBe('hello');
  });

  it('leaves no temp files behind', () => {
    safeWrite(root, 'registry/x.md', 'content', ['registry']);
    const leftovers = fs.readdirSync(path.join(root, 'registry')).filter((f) => f.includes('.tmp'));
    expect(leftovers).toHaveLength(0);
  });

  it('rejects a ../ escape out of the allow-list', () => {
    expect(() => safeWrite(root, 'registry/../secret/leak.md', 'x', ['registry'])).toThrow(
      PathNotAllowedError,
    );
    expect(fs.existsSync(path.join(root, 'secret/leak.md'))).toBe(false);
  });

  it('rejects a path outside any allow-listed dir', () => {
    expect(() => safeWrite(root, 'secret/leak.md', 'x', ['registry', 'taxonomy'])).toThrow(
      PathNotAllowedError,
    );
  });

  it('rejects a symlink escape from inside an allowed dir', () => {
    // registry/sneaky -> ../secret ; writing registry/sneaky/leak.md must be rejected.
    fs.symlinkSync(path.join(root, 'secret'), path.join(root, 'registry', 'sneaky'));
    expect(() => safeWrite(root, 'registry/sneaky/leak.md', 'x', ['registry'])).toThrow(
      PathNotAllowedError,
    );
    expect(fs.existsSync(path.join(root, 'secret/leak.md'))).toBe(false);
  });
});
