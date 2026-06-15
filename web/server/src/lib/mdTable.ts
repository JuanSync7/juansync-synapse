// Parse and serialize a single GitHub pipe-table out of a markdown document.
// Registry files are prose wrapping exactly one inventory table; editing them in
// the web UI means we round-trip the whole file but must guard that the table's
// COLUMN SHAPE is preserved (a dropped/renamed column corrupts the registry and
// silently breaks downstream tooling). sameShape() is that guard.

/** A parsed pipe-table plus the prose surrounding it (preserved verbatim). */
export interface MdTable {
  headers: string[];
  rows: string[][];
  /** Markdown before the table block (verbatim, including trailing newline). */
  beforeText: string;
  /** Markdown after the table block (verbatim). */
  afterText: string;
}

/** A line is table-shaped if its first non-space char is a pipe. */
function isTableLine(line: string): boolean {
  return line.trim().startsWith('|');
}

/** Split a `| a | b |` row into trimmed cells, dropping the edge pipes. */
function splitRow(line: string): string[] {
  const trimmed = line.trim().replace(/^\|/, '').replace(/\|$/, '');
  return trimmed.split('|').map((c) => c.trim());
}

/** A `|---|:--:|` separator line: every cell is dashes/colons only. */
function isSeparatorRow(cells: string[]): boolean {
  return cells.length > 0 && cells.every((c) => /^:?-{1,}:?$/.test(c.replace(/\s/g, '')));
}

/**
 * Find and parse the first pipe-table in `raw`. Returns null when the document
 * contains no header+separator+ table (some registry-class files are pure prose
 * or carry several fragmentary tables — callers treat null as "raw-only, not
 * table-editable").
 */
export function parseMdTable(raw: string): MdTable | null {
  const lines = raw.split('\n');

  for (let i = 0; i < lines.length - 1; i += 1) {
    if (!isTableLine(lines[i] ?? '')) continue;
    const headerCells = splitRow(lines[i] ?? '');
    const sepCells = splitRow(lines[i + 1] ?? '');
    if (!isTableLine(lines[i + 1] ?? '') || !isSeparatorRow(sepCells)) continue;
    if (sepCells.length !== headerCells.length) continue;

    // Header + separator found. Consume contiguous table lines as data rows.
    let end = i + 2;
    const rows: string[][] = [];
    while (end < lines.length && isTableLine(lines[end] ?? '')) {
      rows.push(splitRow(lines[end] ?? ''));
      end += 1;
    }

    // beforeText keeps its trailing newline; afterText keeps its leading one so
    // serialize() can reassemble the exact surrounding prose.
    const beforeText = lines.slice(0, i).join('\n');
    const afterLines = lines.slice(end);
    const afterText = afterLines.length > 0 ? '\n' + afterLines.join('\n') : '';

    return {
      headers: headerCells,
      rows,
      beforeText: beforeText.length > 0 ? beforeText + '\n' : '',
      afterText,
    };
  }

  return null;
}

/** Serialize a parsed table back to GitHub pipe-table markdown + its prose. */
export function serializeMdTable(table: MdTable): string {
  const headerLine = `| ${table.headers.join(' | ')} |`;
  const sepLine = `|${table.headers.map(() => '------').join('|')}|`;
  const rowLines = table.rows.map((r) => `| ${r.join(' | ')} |`);
  const tableText = [headerLine, sepLine, ...rowLines].join('\n');
  return table.beforeText + tableText + table.afterText;
}

/**
 * Guard: do `original` and `edited` parse to a table with the SAME header set
 * (identical column count AND names, in order)? Rejects malformed registry edits
 * that drop/rename a column. If either side has no table, shape can't be
 * guaranteed equal — return false (caller should already have established the
 * original had a table before invoking this).
 */
export function sameShape(original: string, edited: string): boolean {
  const a = parseMdTable(original);
  const b = parseMdTable(edited);
  if (!a || !b) return false;
  if (a.headers.length !== b.headers.length) return false;
  return a.headers.every((h, i) => h === b.headers[i]);
}
