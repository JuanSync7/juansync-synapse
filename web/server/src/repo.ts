import fs from 'node:fs';
import path from 'node:path';

/**
 * Resolve the synapse repo root the server should serve (NFR4).
 *
 * Precedence: `SYNAPSE_REPO` env var if set; otherwise walk upward from cwd
 * until a directory containing a `cortex` file and a `synapse/` directory is
 * found. Throws loudly if neither strategy resolves — the server must never
 * proceed silently against a wrong root.
 */
export function resolveRepoRoot(): string {
  const env = process.env.SYNAPSE_REPO;
  if (env !== undefined && env !== '') {
    return path.resolve(env);
  }

  let dir = process.cwd();
  for (;;) {
    if (looksLikeRepoRoot(dir)) {
      return dir;
    }
    const parent = path.dirname(dir);
    if (parent === dir) {
      throw new Error(
        'Could not resolve synapse repo root: set SYNAPSE_REPO or run inside ' +
          'a checkout (expected a `cortex` file and a `synapse/` directory).',
      );
    }
    dir = parent;
  }
}

function looksLikeRepoRoot(dir: string): boolean {
  try {
    return (
      fs.statSync(path.join(dir, 'cortex')).isFile() &&
      fs.statSync(path.join(dir, 'synapse')).isDirectory()
    );
  } catch {
    return false;
  }
}
