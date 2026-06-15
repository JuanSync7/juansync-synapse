// Registry editor (FR3.1, FR3.4). Left sub-nav of registry files; the selected
// file renders as a table (status chips in the Status column, first-column slugs
// cross-linked to the artifact page) with an Edit toggle to a mono textarea
// carrying Save/Cancel, a dirty indicator, and inline server-error surfacing
// (the 422 shape-mismatch message lands here). On save success we re-fetch.
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import type { ArtifactClass, RegistryDetail, RegistryFile } from '../../../shared/types';
import { getRegistry, listRegistries, putRegistry } from '../api/client';
import DendriteRule from '../components/DendriteRule';
import StatusChip from '../components/StatusChip';

// Map a registry filename to the artifact class its first-column slugs belong
// to, so we can cross-link rows to /artifact/:class/:slug. null = no cross-link.
const CLASS_BY_FILE: Record<string, ArtifactClass> = {
  'SKILL_REGISTRY.md': 'skill',
  'AGENTS_REGISTRY.md': 'agent',
  'PROTOCOL_REGISTRY.md': 'protocol',
  'TOOL_REGISTRY.md': 'tool',
  'PATHWAY_REGISTRY.md': 'pathway',
};

/** Strip a `[slug](path)` markdown link down to the slug; passthrough otherwise. */
function linkSlug(cell: string): string {
  const m = /\[([^\]]+)\]\([^)]*\)/.exec(cell);
  return (m?.[1] ?? cell).trim();
}

function RegistryTableView({ detail }: { detail: RegistryDetail }) {
  const table = detail.table;
  if (!table) {
    return (
      <p className="font-mono text-sm text-muted">
        This file is not a single clean table — switch to Edit to view the raw markdown.
      </p>
    );
  }
  const cls = CLASS_BY_FILE[detail.name];
  const statusIdx = table.headers.findIndex((h) => h.toLowerCase() === 'status');

  return (
    <div className="overflow-x-auto rounded-lg border border-line">
      <table className="w-full border-collapse font-mono text-xs">
        <thead>
          <tr className="border-b border-line bg-surface">
            {table.headers.map((h) => (
              <th key={h} className="px-3 py-2 text-left uppercase tracking-wide text-muted">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, ri) => (
            <tr key={ri} className="border-b border-line/60">
              {row.map((cell, ci) => {
                if (ci === statusIdx) {
                  return (
                    <td key={ci} className="px-3 py-2">
                      <StatusChip status={linkSlug(cell)} />
                    </td>
                  );
                }
                if (ci === 0) {
                  const slug = linkSlug(cell);
                  return (
                    <td key={ci} className="px-3 py-2 text-text">
                      {cls ? (
                        <Link
                          to={`/artifact/${cls}/${slug}`}
                          className="text-synapse hover:underline"
                        >
                          {slug}
                        </Link>
                      ) : (
                        slug
                      )}
                    </td>
                  );
                }
                return (
                  <td key={ci} className="px-3 py-2 text-text/90">
                    {cell}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Registry() {
  const [files, setFiles] = useState<RegistryFile[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<RegistryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Load the file list once; pick the first by default.
  useEffect(() => {
    let cancelled = false;
    listRegistries()
      .then((res) => {
        if (cancelled) return;
        setFiles(res.files);
        setSelected((cur) => cur ?? res.files[0]?.name ?? null);
        setLoading(false);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to load registries');
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Load the selected file's detail (and reset edit state).
  useEffect(() => {
    if (!selected) return;
    let cancelled = false;
    setEditing(false);
    setSaveError(null);
    getRegistry(selected)
      .then((d) => {
        if (cancelled) return;
        setDetail(d);
        setDraft(d.raw);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to load registry file');
      });
    return () => {
      cancelled = true;
    };
  }, [selected]);

  const dirty = detail !== null && draft !== detail.raw;

  function handleSave() {
    if (!selected) return;
    setSaving(true);
    setSaveError(null);
    putRegistry(selected, draft)
      .then(() => getRegistry(selected))
      .then((d) => {
        setDetail(d);
        setDraft(d.raw);
        setEditing(false);
        setSaving(false);
      })
      .catch((e: unknown) => {
        setSaveError(e instanceof Error ? e.message : 'Save failed');
        setSaving(false);
      });
  }

  function handleCancel() {
    if (detail) setDraft(detail.raw);
    setEditing(false);
    setSaveError(null);
  }

  return (
    <section>
      <h1 className="font-display text-4xl font-light tracking-tight text-text">Registry</h1>
      <DendriteRule className="mt-3" />

      {error && (
        <p className="mt-6 rounded border border-membrane bg-membrane/10 px-3 py-2 text-sm text-membrane">
          {error}
        </p>
      )}
      {loading && !error && <p className="mt-6 text-sm text-muted">loading…</p>}

      {!loading && !error && (
        <div className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-[14rem_1fr]">
          <nav
            aria-label="Registry files"
            className="font-mono text-sm lg:sticky lg:top-6 lg:self-start"
          >
            <ul className="space-y-1">
              {files.map((f) => (
                <li key={f.name}>
                  <button
                    type="button"
                    onClick={() => setSelected(f.name)}
                    className={`flex w-full items-center justify-between rounded px-2 py-1 text-left hover:text-synapse ${
                      selected === f.name ? 'text-synapse' : 'text-muted'
                    }`}
                  >
                    <span>{f.name.replace(/\.md$/, '')}</span>
                    {f.kind === 'vocabulary' && (
                      <span className="text-[0.65rem] uppercase text-muted/70">vocab</span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          </nav>

          <div className="lg:border-l lg:border-line lg:pl-8">
            {detail && (
              <>
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="font-mono text-sm text-text">
                    {detail.name}
                    {dirty && <span className="ml-2 text-signal">● unsaved</span>}
                  </h2>
                  {!editing ? (
                    <button
                      type="button"
                      onClick={() => setEditing(true)}
                      className="rounded border border-line px-3 py-1 font-mono text-xs text-text hover:border-synapse/60 hover:text-synapse"
                    >
                      Edit
                    </button>
                  ) : (
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={handleSave}
                        disabled={saving || !dirty}
                        className="rounded border border-synapse bg-synapse/90 px-3 py-1 font-mono text-xs text-ink hover:bg-synapse disabled:opacity-40"
                      >
                        {saving ? 'Saving…' : 'Save'}
                      </button>
                      <button
                        type="button"
                        onClick={handleCancel}
                        className="rounded border border-line px-3 py-1 font-mono text-xs text-muted hover:text-text"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>

                {saveError && (
                  <p className="mb-3 rounded border border-membrane bg-membrane/10 px-3 py-2 font-mono text-xs text-membrane">
                    {saveError}
                  </p>
                )}

                {editing ? (
                  <textarea
                    aria-label="Edit registry markdown"
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    spellCheck={false}
                    className="h-[28rem] w-full resize-y rounded-lg border border-line bg-ink p-3 font-mono text-xs text-text outline-none focus:border-synapse/60"
                  />
                ) : (
                  <RegistryTableView detail={detail} />
                )}
              </>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
