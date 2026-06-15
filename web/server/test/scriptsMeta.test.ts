import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { collectScriptsMeta, parseScriptFrontmatter } from '../src/lib/scriptsMeta';

describe('parseScriptFrontmatter', () => {
  it('parses the `# @key: value` comment head', () => {
    const sh = [
      '#!/usr/bin/env bash',
      '# @name: validate',
      '# @description: Run structural checks without committing',
      '# @audience: contributor',
      '# @action: inspect',
      '# @scope: repo',
      'set -euo pipefail',
      'echo hi',
    ].join('\n');
    const fm = parseScriptFrontmatter(sh);
    expect(fm.name).toBe('validate');
    expect(fm.description).toBe('Run structural checks without committing');
    expect(fm.audience).toBe('contributor');
    expect(fm.action).toBe('inspect');
    expect(fm.scope).toBe('repo');
  });

  it('tolerates a missing head (all null)', () => {
    const fm = parseScriptFrontmatter('echo no frontmatter here');
    expect(fm.name).toBeNull();
    expect(fm.audience).toBeNull();
  });
});

describe('collectScriptsMeta (fixture repo)', () => {
  let root: string;

  beforeEach(() => {
    root = fs.mkdtempSync(path.join(os.tmpdir(), 'scripts-meta-'));
    fs.mkdirSync(path.join(root, 'scripts'), { recursive: true });
    fs.mkdirSync(path.join(root, 'docs', 'cli'), { recursive: true });

    fs.writeFileSync(
      path.join(root, 'scripts', 'validate.sh'),
      [
        '#!/usr/bin/env bash',
        '# @name: validate',
        '# @description: Run structural checks',
        '# @audience: contributor',
        '# @action: inspect',
        '# @scope: repo',
        'echo ok',
      ].join('\n'),
    );
    // A doc that pairs with the validate script.
    fs.writeFileSync(path.join(root, 'docs', 'cli', 'validate.md'), '# cortex validate\n\nUse it.\n');
    // A cli-command doc with no matching .sh.
    fs.writeFileSync(path.join(root, 'docs', 'cli', 'drift.md'), '# cortex drift\n\nResolve drift.\n');
    // README must be ignored.
    fs.writeFileSync(path.join(root, 'docs', 'cli', 'README.md'), '# index\n');
  });

  afterEach(() => fs.rmSync(root, { recursive: true, force: true }));

  it('parses a fixture .sh and pairs its docs/cli file', () => {
    const { scripts } = collectScriptsMeta(root);
    const v = scripts.find((s) => s.name === 'validate');
    expect(v).toBeTruthy();
    expect(v?.kind).toBe('script');
    expect(v?.audience).toBe('contributor');
    expect(v?.path).toBe('scripts/validate.sh');
    expect(v?.doc).toContain('cortex validate');
  });

  it('surfaces cli-command docs that have no matching .sh', () => {
    const { cliCommands } = collectScriptsMeta(root);
    const names = cliCommands.map((c) => c.name);
    expect(names).toContain('drift');
    expect(names).not.toContain('validate'); // validate has a .sh → it's a script, not a cli-command
    expect(names).not.toContain('README');
    const drift = cliCommands.find((c) => c.name === 'drift');
    expect(drift?.kind).toBe('cli-command');
    expect(drift?.doc).toContain('Resolve drift');
  });
});
