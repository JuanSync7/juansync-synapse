// Render parsed EVAL data as checklists grouped into execution / output / other
// criteria. Placeholder evals get a loud banner; missing evals a clean empty
// state. See FR2.1 and DESIGN.md.
import type { Criterion, EvalData } from '../../../shared/types';

function CheckGlyph({ checked }: { checked: boolean }) {
  return (
    <span
      aria-hidden="true"
      className={`mt-0.5 inline-block w-4 shrink-0 font-mono ${
        checked ? 'text-synapse' : 'text-muted'
      }`}
    >
      {checked ? '✓' : '□'}
    </span>
  );
}

function CriterionGroup({ title, items }: { title: string; items: Criterion[] }) {
  if (items.length === 0) return null;
  return (
    <div className="mt-4">
      <h4 className="font-mono text-xs uppercase tracking-wide text-muted">{title}</h4>
      <ul className="mt-2 space-y-1.5">
        {items.map((c) => (
          <li key={c.id} className="flex gap-2 text-sm">
            <CheckGlyph checked={c.checked} />
            <span>
              <span className="font-mono text-xs text-synapse">{c.id}</span>{' '}
              <span className={c.checked ? 'text-text' : 'text-muted'}>{c.text}</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function EvalPanel({ data }: { data: EvalData | null }) {
  if (!data) {
    return (
      <div className="rounded-lg border border-line bg-surface p-4">
        <h3 className="font-display text-lg text-text">Evaluation</h3>
        <p className="mt-2 text-sm text-muted">No EVAL.md found for this artifact.</p>
      </div>
    );
  }

  const { groups } = data;
  const total = groups.execution.length + groups.output.length + groups.other.length;

  return (
    <div className="rounded-lg border border-line bg-surface p-4">
      <h3 className="font-display text-lg text-text">Evaluation</h3>

      {data.isPlaceholder && (
        <div
          role="status"
          className="mt-3 rounded border border-signal bg-signal/10 px-3 py-2 font-mono text-xs uppercase tracking-wide text-signal"
        >
          placeholder EVAL — not yet authored
        </div>
      )}

      {total === 0 ? (
        <p className="mt-2 text-sm text-muted">No criteria parsed.</p>
      ) : (
        <>
          <CriterionGroup title="Execution" items={groups.execution} />
          <CriterionGroup title="Output" items={groups.output} />
          <CriterionGroup title="Other" items={groups.other} />
        </>
      )}
    </div>
  );
}
