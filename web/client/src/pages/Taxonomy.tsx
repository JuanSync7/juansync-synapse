// Taxonomy editor (FR3.2, FR3.4). Lists taxonomy/*.md plus the vocabulary files
// (which live in registry/ but are taxonomy-class editables). View renders the
// markdown; Edit toggles a mono textarea with Save/Cancel, a dirty indicator,
// and inline server-error surfacing. On save success we re-fetch.
import { useEffect, useState } from 'react';
import type { TaxonomyDetail, TaxonomyFile } from '../../../shared/types';
import { getTaxonomy, listTaxonomies, putTaxonomy } from '../api/client';
import DendriteRule from '../components/DendriteRule';
import Markdown from '../components/Markdown';

export default function Taxonomy() {
  const [files, setFiles] = useState<TaxonomyFile[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<TaxonomyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    listTaxonomies()
      .then((res) => {
        if (cancelled) return;
        setFiles(res.files);
        setSelected((cur) => cur ?? res.files[0]?.name ?? null);
        setLoading(false);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to load taxonomies');
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selected) return;
    let cancelled = false;
    setEditing(false);
    setSaveError(null);
    getTaxonomy(selected)
      .then((d) => {
        if (cancelled) return;
        setDetail(d);
        setDraft(d.raw);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to load taxonomy file');
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
    putTaxonomy(selected, draft)
      .then(() => getTaxonomy(selected))
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
      <h1 className="font-display text-4xl font-light tracking-tight text-text">Taxonomy</h1>
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
            aria-label="Taxonomy files"
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
                    aria-label="Edit taxonomy markdown"
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    spellCheck={false}
                    className="h-[28rem] w-full resize-y rounded-lg border border-line bg-ink p-3 font-mono text-xs text-text outline-none focus:border-synapse/60"
                  />
                ) : (
                  <Markdown>{detail.raw}</Markdown>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
