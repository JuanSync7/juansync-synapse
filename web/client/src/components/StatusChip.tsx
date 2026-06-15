// Status chip: stable (solid green fill), draft (hollow amber outline),
// anything else (muted). See DESIGN.md "Badges".

export default function StatusChip({ status }: { status: string }) {
  const s = (status || '').toLowerCase();
  let className: string;
  if (s === 'stable' || s === 'active') {
    className = 'bg-synapse/90 text-ink border-synapse';
  } else if (s === 'draft') {
    className = 'border-signal text-signal';
  } else {
    className = 'border-muted text-muted';
  }
  return (
    <span
      className={`inline-block rounded border px-2 py-0.5 font-mono text-[0.7rem] uppercase tracking-wide ${className}`}
    >
      {status || 'unknown'}
    </span>
  );
}
