// Memo board (FR5.3). Memos grouped by brainstorm session / change_requests dir,
// an All/Executed/Pending status filter with live counts, and a per-row execute
// toggle that PATCHes optimistically (reverting on error → membrane red). Click a
// row to open a detail panel with the rendered markdown body, the toggle, and a
// (disabled) "Run creator with this memo" button that slice S9 will wire to a
// real creator run. Executed = synapse green check; pending = signal amber.
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import type { Memo, MemoCounts } from '../../../shared/types';
import { getMemo, listMemos, setMemoExecuted } from '../api/client';
import DendriteRule from '../components/DendriteRule';
import Markdown from '../components/Markdown';

type Filter = 'all' | 'executed' | 'pending';

/** Group memos by their source (brainstorm session or change_requests dir). */
function groupBySource(memos: Memo[]): [string, Memo[]][] {
  const groups = new Map<string, Memo[]>();
  for (const m of memos) {
    const list = groups.get(m.source) ?? [];
    list.push(m);
    groups.set(m.source, list);
  }
  return [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0]));
}

function ArtifactTypeBadge({ type }: { type: string | null }) {
  if (!type) return null;
  return (
    <span className="rounded border border-line px-1.5 py-0.5 font-mono text-[0.65rem] uppercase tracking-wide text-muted">
      {type}
    </span>
  );
}

function MemoRow({
  memo,
  onToggle,
  onOpen,
  selected,
}: {
  memo: Memo;
  onToggle: (memo: Memo, next: boolean) => void;
  onOpen: (memo: Memo) => void;
  selected: boolean;
}) {
  return (
    <div
      className={`flex items-center gap-3 border-b border-line/60 px-3 py-2 ${
        selected ? 'bg-surface' : ''
      }`}
    >
      <input
        type="checkbox"
        aria-label={`Mark ${memo.title} executed`}
        checked={memo.executed}
        disabled={!memo.path}
        onChange={(e) => onToggle(memo, e.target.checked)}
        className="h-4 w-4 shrink-0 accent-[#5DF2A1] disabled:opacity-30"
      />
      <button
        type="button"
        data-testid="memo-open"
        onClick={() => onOpen(memo)}
        className="flex flex-1 items-center justify-between gap-3 text-left"
      >
        <span className="min-w-0">
          <span className="block truncate font-mono text-sm text-text hover:text-synapse">
            {memo.title}
          </span>
          {memo.createdDate && (
            <span className="font-mono text-[0.65rem] text-muted">{memo.createdDate}</span>
          )}
        </span>
        <span className="flex shrink-0 items-center gap-2">
          <ArtifactTypeBadge type={memo.artifactType} />
          <span
            className={`font-mono text-[0.7rem] ${
              memo.executed ? 'text-synapse' : 'text-signal'
            }`}
          >
            {memo.executed ? '✓ executed' : '○ pending'}
          </span>
        </span>
      </button>
    </div>
  );
}

function MemoDrawer({
  memo,
  onClose,
  onToggle,
}: {
  memo: Memo;
  onClose: () => void;
  onToggle: (memo: Memo, next: boolean) => void;
}) {
  const [body, setBody] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setBody(null);
    setError(null);
    getMemo(memo.id)
      .then((d) => {
        if (!cancelled) setBody(d.body);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load memo');
      });
    return () => {
      cancelled = true;
    };
  }, [memo.id]);

  return (
    <aside
      aria-label="Memo detail"
      className="rounded-lg border border-line bg-surface p-5"
    >
      <div className="mb-3 flex items-start justify-between gap-3">
        <h2 className="font-mono text-sm text-text">{memo.title}</h2>
        <button
          type="button"
          onClick={onClose}
          className="font-mono text-xs text-muted hover:text-text"
        >
          close
        </button>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-3 font-mono text-[0.7rem] text-muted">
        <span>{memo.source}</span>
        <ArtifactTypeBadge type={memo.artifactType} />
        <label className="flex items-center gap-1.5">
          <input
            type="checkbox"
            checked={memo.executed}
            disabled={!memo.path}
            onChange={(e) => onToggle(memo, e.target.checked)}
            className="h-4 w-4 accent-[#5DF2A1] disabled:opacity-30"
          />
          <span className={memo.executed ? 'text-synapse' : 'text-signal'}>
            {memo.executed ? 'executed' : 'pending'}
          </span>
        </label>
      </div>

      {/* Hand off to the creator-run surface (FR7) preselected to this memo.
          The run itself is started there (POST /api/runs/creator). */}
      <Link
        to={`/runs?memo=${encodeURIComponent(memo.id)}`}
        className="mb-4 inline-block rounded border border-synapse px-3 py-1 font-mono text-xs text-synapse hover:bg-synapse/10"
      >
        Run creator with this memo
      </Link>

      {error && (
        <p className="rounded border border-membrane bg-membrane/10 px-3 py-2 font-mono text-xs text-membrane">
          {error}
        </p>
      )}
      {body === null && !error && <p className="font-mono text-xs text-muted">loading…</p>}
      {body !== null && <Markdown>{body}</Markdown>}
    </aside>
  );
}

export default function Memos() {
  const [memos, setMemos] = useState<Memo[]>([]);
  const [counts, setCounts] = useState<MemoCounts | null>(null);
  const [filter, setFilter] = useState<Filter>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [patchError, setPatchError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listMemos()
      .then((res) => {
        if (cancelled) return;
        setMemos(res.memos);
        setCounts(res.counts);
        setLoading(false);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to load memos');
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const visible = useMemo(() => {
    if (filter === 'executed') return memos.filter((m) => m.executed);
    if (filter === 'pending') return memos.filter((m) => !m.executed);
    return memos;
  }, [memos, filter]);

  const groups = useMemo(() => groupBySource(visible), [visible]);
  const selected = memos.find((m) => m.id === selectedId) ?? null;

  function recount(next: Memo[]): MemoCounts {
    return {
      total: next.length,
      executed: next.filter((m) => m.executed).length,
      pending: next.filter((m) => !m.executed).length,
    };
  }

  // Optimistic toggle: flip locally, PATCH, revert + surface error on failure.
  function handleToggle(memo: Memo, next: boolean) {
    setPatchError(null);
    const optimistic = memos.map((m) => (m.id === memo.id ? { ...m, executed: next } : m));
    setMemos(optimistic);
    setCounts(recount(optimistic));

    setMemoExecuted(memo.id, next)
      .then((updated) => {
        setMemos((cur) => {
          const merged = cur.map((m) => (m.id === updated.id ? updated : m));
          setCounts(recount(merged));
          return merged;
        });
      })
      .catch((e: unknown) => {
        // Revert to the pre-toggle value.
        setMemos((cur) => {
          const reverted = cur.map((m) => (m.id === memo.id ? { ...m, executed: !next } : m));
          setCounts(recount(reverted));
          return reverted;
        });
        setPatchError(e instanceof Error ? e.message : 'Toggle failed');
      });
  }

  const FILTERS: [Filter, string, number | undefined][] = [
    ['all', 'All', counts?.total],
    ['executed', 'Executed', counts?.executed],
    ['pending', 'Pending', counts?.pending],
  ];

  return (
    <section>
      <h1 className="font-display text-4xl font-light tracking-tight text-text">Memos</h1>
      <DendriteRule className="mt-3" />

      {error && (
        <p className="mt-6 rounded border border-membrane bg-membrane/10 px-3 py-2 text-sm text-membrane">
          {error}
        </p>
      )}
      {loading && !error && <p className="mt-6 text-sm text-muted">loading…</p>}

      {!loading && !error && (
        <>
          <div className="mt-6 flex items-center gap-2 font-mono text-xs">
            {FILTERS.map(([key, label, n]) => (
              <button
                key={key}
                type="button"
                onClick={() => setFilter(key)}
                className={`rounded border px-3 py-1 ${
                  filter === key
                    ? 'border-synapse text-synapse'
                    : 'border-line text-muted hover:text-text'
                }`}
              >
                {label}
                {n !== undefined && <span className="ml-1.5 text-muted/70">{n}</span>}
              </button>
            ))}
          </div>

          {patchError && (
            <p className="mt-4 rounded border border-membrane bg-membrane/10 px-3 py-2 font-mono text-xs text-membrane">
              {patchError}
            </p>
          )}

          <div className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-[1fr_1fr]">
            <div>
              {groups.length === 0 && (
                <p className="font-mono text-sm text-muted">No memos in this view.</p>
              )}
              {groups.map(([source, items]) => (
                <div key={source} className="mb-6">
                  <h2 className="mb-1 font-mono text-xs uppercase tracking-wide text-synapse/80">
                    {source}
                  </h2>
                  <div className="rounded-lg border border-line">
                    {items.map((m) => (
                      <MemoRow
                        key={m.id}
                        memo={m}
                        selected={m.id === selectedId}
                        onToggle={handleToggle}
                        onOpen={(memo) => setSelectedId(memo.id)}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="lg:border-l lg:border-line lg:pl-8">
              {selected ? (
                <MemoDrawer
                  memo={selected}
                  onClose={() => setSelectedId(null)}
                  onToggle={handleToggle}
                />
              ) : (
                <p className="font-mono text-sm text-muted">Select a memo to view it.</p>
              )}
            </div>
          </div>
        </>
      )}
    </section>
  );
}
