import fs from 'node:fs';
import path from 'node:path';
import type { CliCommandMeta, ScriptMeta } from '../../../shared/types';

/** The five comment-frontmatter keys scripts/*.sh carry (FR8.1). */
export interface ScriptFrontmatter {
  name: string | null;
  description: string | null;
  audience: string | null;
  action: string | null;
  scope: string | null;
}

const KEY_RE = /^#\s*@(name|description|audience|action|scope):\s*(.*)$/;

/**
 * Parse the `# @key: value` comment head of a shell script. We scan only the
 * leading comment block (stop at the first non-comment, non-shebang, non-blank
 * line) because the keys live in the file header and a deeper scan would risk
 * picking up unrelated `# @…` mentions in the body. Missing keys yield null —
 * tolerant by design so a script without a full head still lists.
 */
export function parseScriptFrontmatter(text: string): ScriptFrontmatter {
  const fm: ScriptFrontmatter = {
    name: null,
    description: null,
    audience: null,
    action: null,
    scope: null,
  };
  for (const line of text.split(/\r?\n/)) {
    if (line.startsWith('#!')) continue;
    if (line.trim() === '') continue;
    if (!line.startsWith('#')) break; // left the comment head
    const m = KEY_RE.exec(line);
    if (m) {
      const key = m[1] as keyof ScriptFrontmatter;
      fm[key] = (m[2] ?? '').trim() || null;
    }
  }
  return fm;
}

/**
 * Collect the scripts control-panel inventory (FR8.1):
 *  - every scripts/*.sh, parsed for its comment head + paired with
 *    docs/cli/<name>.md when present;
 *  - the cortex python-CLI command groups: docs/cli/*.md that do NOT correspond
 *    to a .sh file (drift, pins, doctor, clerk, telemetry, pathway, …). These
 *    are documentation-only command groups handled by the python dispatcher,
 *    not shell scripts.
 */
export function collectScriptsMeta(repoRoot: string): {
  scripts: ScriptMeta[];
  cliCommands: CliCommandMeta[];
} {
  const scriptsDir = path.join(repoRoot, 'scripts');
  const cliDir = path.join(repoRoot, 'docs', 'cli');

  // Index docs/cli/*.md by base name (sans extension), README excluded.
  const docByName = new Map<string, string>();
  for (const file of listMd(cliDir)) {
    const name = path.basename(file, '.md');
    if (name === 'README') continue;
    docByName.set(name, read(path.join(cliDir, file)));
  }

  const scripts: ScriptMeta[] = [];
  const scriptNames = new Set<string>();
  for (const file of listSh(scriptsDir)) {
    const abs = path.join(scriptsDir, file);
    const fm = parseScriptFrontmatter(read(abs));
    // Fall back to the filename (sans .sh) when @name is absent.
    const name = fm.name ?? path.basename(file, '.sh');
    scriptNames.add(name);
    scripts.push({
      kind: 'script',
      name,
      description: fm.description,
      audience: fm.audience,
      action: fm.action,
      scope: fm.scope,
      path: `scripts/${file}`,
      doc: docByName.get(name) ?? null,
    });
  }
  scripts.sort((a, b) => a.name.localeCompare(b.name));

  // cli-commands: docs/cli entries whose name has no matching script.
  const cliCommands: CliCommandMeta[] = [];
  for (const [name, doc] of docByName) {
    if (scriptNames.has(name)) continue;
    cliCommands.push({ kind: 'cli-command', name, doc });
  }
  cliCommands.sort((a, b) => a.name.localeCompare(b.name));

  return { scripts, cliCommands };
}

function listSh(dir: string): string[] {
  try {
    return fs
      .readdirSync(dir, { withFileTypes: true })
      .filter((e) => e.isFile() && e.name.endsWith('.sh'))
      .map((e) => e.name);
  } catch {
    return [];
  }
}

function listMd(dir: string): string[] {
  try {
    return fs
      .readdirSync(dir, { withFileTypes: true })
      .filter((e) => e.isFile() && e.name.endsWith('.md'))
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
