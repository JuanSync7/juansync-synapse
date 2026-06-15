import type { Criterion, EvalData, EvalGroups } from '../../../shared/types';

// A checklist line: `- [ ] text` or `- [x] text` (any indentation).
const CHECKLIST_RE = /^[ \t]*-[ \t]+\[([ xX])\][ \t]+(.*)$/;
// EVAL ids: EVAL-E01 (execution) / EVAL-O01 (output). Captured anywhere in text.
const EXEC_ID_RE = /\bEVAL-E\d+\b/;
const OUTPUT_ID_RE = /\bEVAL-O\d+\b/;
const ANY_ID_RE = /\bEVAL-[A-Z]\d+\b/;

const PLACEHOLDER_RE = /todo|placeholder/i;
const MIN_REAL_LENGTH = 200;

/**
 * Parse an EVAL.md body into grouped criteria. The eval-writer emits checklist
 * lines tagged with `EVAL-Exx` (execution) and `EVAL-Oxx` (output) ids; any
 * other checklist item lands in `other`. We classify by id prefix rather than
 * section heading because heading wording drifts across artifacts but the id
 * grammar is stable.
 *
 * `isPlaceholder` flags evals that aren't real yet — too short to be meaningful
 * or carrying TODO/placeholder text — so the UI can visibly mark missing
 * coverage (FR2.1) instead of presenting a hollow checklist as complete.
 */
export function parseEval(raw: string): EvalData {
  const groups: EvalGroups = { execution: [], output: [], other: [] };

  for (const line of raw.split(/\r?\n/)) {
    const m = CHECKLIST_RE.exec(line);
    if (!m) continue;

    const checked = m[1]?.toLowerCase() === 'x';
    const rawText = (m[2] ?? '').trim();

    const execId = EXEC_ID_RE.exec(rawText);
    const outId = OUTPUT_ID_RE.exec(rawText);

    if (execId) {
      groups.execution.push(makeCriterion(execId[0], rawText, checked));
    } else if (outId) {
      groups.output.push(makeCriterion(outId[0], rawText, checked));
    } else {
      const anyId = ANY_ID_RE.exec(rawText);
      groups.other.push(makeCriterion(anyId ? anyId[0] : '', rawText, checked));
    }
  }

  const isPlaceholder = raw.length < MIN_REAL_LENGTH || PLACEHOLDER_RE.test(raw);
  return { raw, groups, isPlaceholder };
}

function makeCriterion(id: string, rawText: string, checked: boolean): Criterion {
  // Strip a leading `**EVAL-X01:**` (or unbolded) label so the displayed text
  // is the criterion prose, not the id we already captured separately.
  let text = rawText;
  if (id) {
    text = text
      .replace(new RegExp(`\\*\\*${id}:?\\*\\*`), '')
      .replace(new RegExp(`${id}:?`), '')
      .trim();
  }
  // Drop residual leading markdown emphasis/colon punctuation.
  text = text.replace(/^[\s:*]+/, '').trim();
  return { id, text, checked };
}
