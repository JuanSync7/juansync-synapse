// Layer provenance badge: base (synapse/) green, addon (src/) amber, external
// (external/) blue-grey. Outline style, never a wash. See DESIGN.md "Badges".
import type { Layer } from '../../../shared/types';

const STYLE: Record<Layer, { label: string; className: string }> = {
  base: { label: 'base', className: 'border-synapse text-synapse' },
  addon: { label: 'add-on', className: 'border-signal text-signal' },
  external: { label: 'external', className: 'border-muted text-muted' },
};

export default function LayerBadge({ layer }: { layer: Layer }) {
  const s = STYLE[layer] ?? STYLE.external;
  return (
    <span
      className={`inline-block rounded-full border px-2 py-0.5 font-mono text-[0.7rem] uppercase tracking-wide ${s.className}`}
    >
      {s.label}
    </span>
  );
}
