// Generic artifact browser, parameterized by class (FR1.3). Free-text search +
// layer / domain / status filters. Search & layer & domain hit the API; status
// is filtered client-side (the index carries it but the endpoint doesn't). Empty
// results show a clean empty-state (matters for the persona class under /skills).
import { useEffect, useMemo, useState } from 'react';
import type { Artifact, ArtifactClass } from '../../../shared/types';
import { listArtifacts } from '../api/client';
import ArtifactCard from '../components/ArtifactCard';
import DendriteRule from '../components/DendriteRule';

const TITLES: Record<ArtifactClass, string> = {
  skill: 'Skills',
  agent: 'Agents',
  protocol: 'Protocols',
  tool: 'Tools',
  pathway: 'Pathways',
};

export default function ArtifactList({ cls }: { cls: ArtifactClass }) {
  const [items, setItems] = useState<Artifact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [q, setQ] = useState('');
  const [layer, setLayer] = useState('');
  const [domain, setDomain] = useState('');
  const [status, setStatus] = useState('');

  // Re-fetch on class / server-side filter change. q is debounced via the
  // effect dependency directly — simple and adequate for a localhost tool.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    listArtifacts({
      class: cls,
      q: q || undefined,
      layer: layer || undefined,
      domain: domain || undefined,
    })
      .then((res) => {
        if (cancelled) return;
        setItems(res.items);
        setLoading(false);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to load artifacts');
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [cls, q, layer, domain]);

  // Domain options derive from whatever is currently loaded (no separate query).
  const domains = useMemo(
    () => Array.from(new Set(items.map((a) => a.domain).filter((d): d is string => !!d))).sort(),
    [items],
  );

  const visible = useMemo(
    () => (status ? items.filter((a) => a.status.toLowerCase() === status) : items),
    [items, status],
  );

  return (
    <section className="mx-auto max-w-6xl">
      <h1 className="font-display text-4xl font-light tracking-tight text-text">
        {TITLES[cls]}
      </h1>
      <DendriteRule className="mt-3" />

      <div className="mt-6 flex flex-wrap gap-3">
        <input
          type="search"
          aria-label="Search"
          placeholder="search slug or description…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="flex-1 min-w-[14rem] rounded border border-line bg-surface px-3 py-1.5 font-mono text-sm text-text outline-none placeholder:text-muted/60 focus:border-synapse/60"
        />
        <select
          aria-label="Layer"
          value={layer}
          onChange={(e) => setLayer(e.target.value)}
          className="rounded border border-line bg-surface px-2 py-1.5 font-mono text-sm text-text outline-none focus:border-synapse/60"
        >
          <option value="">all layers</option>
          <option value="base">base</option>
          <option value="addon">add-on</option>
          <option value="external">external</option>
        </select>
        <select
          aria-label="Domain"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          className="rounded border border-line bg-surface px-2 py-1.5 font-mono text-sm text-text outline-none focus:border-synapse/60"
        >
          <option value="">all domains</option>
          {domains.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        <select
          aria-label="Status"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded border border-line bg-surface px-2 py-1.5 font-mono text-sm text-text outline-none focus:border-synapse/60"
        >
          <option value="">all status</option>
          <option value="stable">stable</option>
          <option value="draft">draft</option>
        </select>
      </div>

      {error && (
        <p className="mt-6 rounded border border-membrane bg-membrane/10 px-3 py-2 text-sm text-membrane">
          {error}
        </p>
      )}

      {!error && loading && <p className="mt-6 text-sm text-muted">loading…</p>}

      {!error && !loading && visible.length === 0 && (
        <div className="mt-10 rounded-lg border border-dashed border-line px-6 py-10 text-center">
          <p className="font-display text-lg text-muted">No {cls}s here yet.</p>
          <p className="mt-1 text-sm text-muted/70">
            This class is scaffolded but empty in the current overlay.
          </p>
        </div>
      )}

      {!error && !loading && visible.length > 0 && (
        <>
          <p className="mt-6 font-mono text-xs text-muted">
            {visible.length} {visible.length === 1 ? 'artifact' : 'artifacts'}
          </p>
          <ul className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {visible.map((a, i) => (
              <ArtifactCard key={`${a.class}/${a.slug}`} artifact={a} index={i} />
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
