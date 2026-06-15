import { describe, expect, it } from 'vitest';
import { parseMdTable, serializeMdTable, sameShape } from '../src/lib/mdTable';

const DOC = `# Title

Some intro prose.

| Skill | Description | Status |
|-------|-------------|--------|
| [a](p) | does a | stable |
| [b](p) | does b | draft |

Trailing prose after the table.
`;

describe('parseMdTable', () => {
  it('parses headers, rows, and surrounding prose', () => {
    const t = parseMdTable(DOC);
    expect(t).not.toBeNull();
    expect(t!.headers).toEqual(['Skill', 'Description', 'Status']);
    expect(t!.rows).toHaveLength(2);
    expect(t!.rows[0]).toEqual(['[a](p)', 'does a', 'stable']);
    expect(t!.beforeText).toContain('Some intro prose.');
    expect(t!.afterText).toContain('Trailing prose');
  });

  it('returns null when there is no table', () => {
    expect(parseMdTable('# Just prose\n\nno table here.\n')).toBeNull();
  });
});

describe('serializeMdTable round-trip', () => {
  it('re-parses to an identical table after serialize', () => {
    const t = parseMdTable(DOC)!;
    const out = serializeMdTable(t);
    const again = parseMdTable(out)!;
    expect(again.headers).toEqual(t.headers);
    expect(again.rows).toEqual(t.rows);
    expect(out).toContain('Some intro prose.');
    expect(out).toContain('Trailing prose after the table.');
  });
});

describe('sameShape', () => {
  it('accepts an edit that preserves the columns', () => {
    const edited = DOC.replace('| does a |', '| does A now |');
    expect(sameShape(DOC, edited)).toBe(true);
  });

  it('rejects an edit that drops a column', () => {
    const dropped = `# Title

Some intro prose.

| Skill | Description |
|-------|-------------|
| [a](p) | does a |

Trailing prose after the table.
`;
    expect(sameShape(DOC, dropped)).toBe(false);
  });

  it('rejects an edit that renames a column', () => {
    const renamed = DOC.replace('| Status |', '| State |');
    expect(sameShape(DOC, renamed)).toBe(false);
  });
});
