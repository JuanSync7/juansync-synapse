import { describe, expect, it } from 'vitest';
import { parseEval } from '../src/lib/evalParse';

const FIXTURE = `# foo — Evaluation Criteria

Some preamble that is long enough so the file is not flagged merely for being
short. Filler filler filler filler filler filler filler filler filler text.

## Execution Criteria

- [ ] **EVAL-E01:** does the thing
  - Test: it does the thing
- [x] **EVAL-E02:** does another thing

## Output Criteria

- [x] **EVAL-O01:** output has a heading
- [ ] **EVAL-O02:** output is verifiable

## Other

- [ ] a loose checklist item with no id
`;

describe('parseEval', () => {
  it('routes EVAL-E ids to execution, EVAL-O to output, the rest to other', () => {
    const r = parseEval(FIXTURE);
    expect(r.groups.execution.map((c) => c.id)).toEqual(['EVAL-E01', 'EVAL-E02']);
    expect(r.groups.output.map((c) => c.id)).toEqual(['EVAL-O01', 'EVAL-O02']);
    expect(r.groups.other.length).toBe(1);
  });

  it('captures checked state', () => {
    const r = parseEval(FIXTURE);
    expect(r.groups.execution.find((c) => c.id === 'EVAL-E02')?.checked).toBe(true);
    expect(r.groups.execution.find((c) => c.id === 'EVAL-E01')?.checked).toBe(false);
    expect(r.groups.output.find((c) => c.id === 'EVAL-O01')?.checked).toBe(true);
  });

  it('strips id markup from criterion text', () => {
    const r = parseEval(FIXTURE);
    expect(r.groups.execution[0]?.text).toContain('does the thing');
    expect(r.groups.execution[0]?.text).not.toContain('EVAL-E01');
  });

  it('is not a placeholder for a long real file', () => {
    expect(parseEval(FIXTURE).isPlaceholder).toBe(false);
  });

  it('flags short files as placeholders', () => {
    expect(parseEval('# stub').isPlaceholder).toBe(true);
  });

  it('flags files containing TODO/placeholder text', () => {
    const long = '# eval\n\n'.padEnd(300, 'x') + '\n\nTODO: write criteria';
    expect(parseEval(long).isPlaceholder).toBe(true);
  });
});
