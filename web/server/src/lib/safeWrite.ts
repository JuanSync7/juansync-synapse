// The ONLY write path for registry/taxonomy edits (NFR5, DESIGN.md decision #3).
// Every PUT funnels through here so the path allow-list and atomic-write
// guarantees live in exactly one place. Without realpath-based containment, a
// crafted `..` path or a symlink inside an allowed dir could escape the
// allow-list and let the UI overwrite arbitrary repo files.
import fs from 'node:fs';
import path from 'node:path';

/** Thrown when a write target resolves outside every allow-listed directory. */
export class PathNotAllowedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'PathNotAllowedError';
  }
}

/**
 * realpath the directory, falling back to the nearest existing ancestor when the
 * leaf doesn't exist yet. This resolves symlinks in the real prefix so a symlink
 * escape is caught, while still allowing writes to not-yet-created files.
 */
function realDir(dir: string): string {
  let cur = path.resolve(dir);
  for (;;) {
    try {
      return fs.realpathSync(cur);
    } catch {
      const parent = path.dirname(cur);
      if (parent === cur) return cur; // hit filesystem root; give up resolving
      cur = parent;
    }
  }
}

/** True when `child` is `parent` or nested under it (path-segment safe). */
function isInside(parent: string, child: string): boolean {
  const rel = path.relative(parent, child);
  return rel === '' || (!rel.startsWith('..') && !path.isAbsolute(rel));
}

/**
 * Atomically write `content` to `relPath` under `repoRoot`, asserting the
 * resolved absolute path sits inside one of `allowDirs` (each relative to
 * repoRoot). Rejects `..` escapes and symlink escapes via realpath containment.
 * Atomic = write a temp file in the SAME directory then rename (rename is atomic
 * within a filesystem, so a reader never sees a half-written registry).
 */
export function safeWrite(
  repoRoot: string,
  relPath: string,
  content: string,
  allowDirs: string[],
): void {
  const absTarget = path.resolve(repoRoot, relPath);
  const targetDir = path.dirname(absTarget);
  const realTargetDir = realDir(targetDir);

  const allowed = allowDirs.some((d) => {
    const realAllow = realDir(path.resolve(repoRoot, d));
    return isInside(realAllow, realTargetDir);
  });

  if (!allowed) {
    throw new PathNotAllowedError(
      `Refusing to write outside the allow-list: ${relPath} (resolved to ${absTarget})`,
    );
  }

  const tmp = path.join(
    realTargetDir,
    `.${path.basename(absTarget)}.${process.pid}.${Date.now()}.tmp`,
  );
  fs.writeFileSync(tmp, content, 'utf8');
  try {
    fs.renameSync(tmp, path.join(realTargetDir, path.basename(absTarget)));
  } catch (err) {
    // Clean up the temp file on a failed rename so we never leave litter.
    try {
      fs.unlinkSync(tmp);
    } catch {
      /* already gone */
    }
    throw err;
  }
}
