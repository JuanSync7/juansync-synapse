import { parse as parseYaml } from 'yaml';

/** Result of splitting a markdown file into frontmatter + body. */
export interface ParsedFrontmatter {
  /** Parsed YAML object, or {} when absent/malformed/non-object. */
  data: Record<string, unknown>;
  /** Markdown after the closing fence (or the whole input if no frontmatter). */
  body: string;
  /** The original input, verbatim. */
  raw: string;
}

// Matches a leading `---` fenced YAML block. The body is everything after the
// closing fence. We deliberately tolerate trailing whitespace on fence lines.
const FRONTMATTER_RE = /^---[ \t]*\r?\n([\s\S]*?)\r?\n---[ \t]*\r?\n?/;

/**
 * Tolerant frontmatter parser. Skills, tools, memos, and protocols all carry a
 * `---` fenced YAML head; the rest of the file is body markdown. Crawling the
 * whole repo means we will hit half-written and malformed files — so this never
 * throws: a missing or unparseable block yields `data = {}` and the original
 * text as the body. Without this tolerance one bad artifact would 500 the whole
 * artifacts list.
 */
export function parseFrontmatter(raw: string): ParsedFrontmatter {
  const match = FRONTMATTER_RE.exec(raw);
  if (!match) {
    return { data: {}, body: raw, raw };
  }

  const yamlText = match[1] ?? '';
  const body = raw.slice(match[0].length);

  let data: Record<string, unknown> = {};
  try {
    const parsed = parseYaml(yamlText);
    if (parsed !== null && typeof parsed === 'object' && !Array.isArray(parsed)) {
      data = parsed as Record<string, unknown>;
    }
  } catch {
    data = {};
  }

  return { data, body, raw };
}
