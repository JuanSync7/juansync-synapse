// Artifact detail: asymmetric two-column split — rendered body (2/3) + a right
// rail (1/3) carrying frontmatter, badges, aliases, companions, registry row and
// the EVAL panel. Pathways additionally render their inherits-resolved bundle.
// FR1.3, FR1.4, FR2.1.
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import type {
  ArtifactClass,
  ArtifactDetail as Detail,
  Companion,
  ResolvedPathway,
} from '../../../shared/types';
import { getArtifact } from '../api/client';
import DendriteRule from '../components/DendriteRule';
import EvalPanel from '../components/EvalPanel';
import LayerBadge from '../components/LayerBadge';
import Markdown from '../components/Markdown';
import StatusChip from '../components/StatusChip';

const VALID: readonly ArtifactClass[] = ['skill', 'agent', 'protocol', 'tool', 'pathway'];

function isClass(v: string | undefined): v is ArtifactClass {
  return !!v && (VALID as readonly string[]).includes(v);
}

function RailCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4 shadow-sm">
      <h3 className="text-[0.7rem] font-semibold uppercase tracking-wider text-muted">{title}</h3>
      <div className="mt-3">{children}</div>
    </div>
  );
}

/** Format a frontmatter/registry value for display. Arrays render as a clean
 *  comma list (not a JSON blob); objects fall back to compact JSON. */
function formatValue(v: unknown): string {
  if (typeof v === 'string') return v;
  if (typeof v === 'number' || typeof v === 'boolean') return String(v);
  if (Array.isArray(v)) return v.map((x) => (typeof x === 'string' ? x : JSON.stringify(x))).join(', ');
  return JSON.stringify(v);
}

/** Stacked key/value list: label above, value below at full card width. Long
 *  prose values (e.g. description) read as sans paragraphs; short identifiers
 *  stay mono so they read like the data atoms they are. */
function KeyValueList({ entries }: { entries: [string, unknown][] }) {
  return (
    <dl className="space-y-3">
      {entries.map(([k, v]) => {
        const value = formatValue(v);
        const isProse = value.length > 48 && !/^[\w./:@-]+$/.test(value);
        return (
          <div key={k}>
            <dt className="text-[0.68rem] font-medium uppercase tracking-wider text-muted">{k}</dt>
            <dd
              className={`mt-0.5 break-words text-text ${
                isProse ? 'text-[0.82rem] leading-relaxed' : 'font-mono text-xs leading-relaxed'
              }`}
            >
              {value}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}

function FrontmatterCard({ fm }: { fm: Record<string, unknown> }) {
  // `aliases` has its own card; `description` is already the page subtitle.
  const entries = Object.entries(fm).filter(([k]) => k !== 'aliases' && k !== 'description');
  if (entries.length === 0) return null;
  return (
    <RailCard title="Frontmatter">
      <KeyValueList entries={entries} />
    </RailCard>
  );
}

const KIND_LABEL: Record<Companion['kind'], string> = {
  reference: 'references',
  template: 'templates',
  schema: 'schemas',
  cli: 'cli',
  other: 'other',
};

function CompanionTree({ companions }: { companions: Companion[] }) {
  if (companions.length === 0) return null;
  const groups = new Map<Companion['kind'], Companion[]>();
  for (const c of companions) {
    const list = groups.get(c.kind) ?? [];
    list.push(c);
    groups.set(c.kind, list);
  }
  return (
    <RailCard title="Companion files">
      <ul className="space-y-2 font-mono text-xs">
        {Array.from(groups.entries()).map(([kind, files]) => (
          <li key={kind}>
            <span className="text-muted">{KIND_LABEL[kind]}/</span>
            <ul className="mt-1 space-y-0.5 pl-3">
              {files.map((f) => (
                <li key={f.path} className="text-text" title={f.path}>
                  {f.name}
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </RailCard>
  );
}

function PathwayResolved({ resolved }: { resolved: ResolvedPathway }) {
  const groups = (
    [
      { cls: 'skill', label: 'skills', slugs: resolved.skills },
      { cls: 'agent', label: 'agents', slugs: resolved.agents },
      { cls: 'protocol', label: 'protocols', slugs: resolved.protocols },
      { cls: 'tool', label: 'tools', slugs: resolved.tools },
    ] satisfies { cls: ArtifactClass; label: string; slugs: string[] }[]
  ).filter((g) => g.slugs.length > 0);

  return (
    <RailCard title="Resolved bundle">
      <div className="space-y-3 text-sm">
        {groups.map((g) => (
          <div key={g.cls}>
            <p className="font-mono text-xs text-muted">{g.label}</p>
            <ul className="mt-1 space-y-0.5">
              {g.slugs.map((s) => (
                <li key={s}>
                  <Link
                    to={`/artifact/${g.cls}/${s}`}
                    className="font-mono text-xs text-synapse hover:underline"
                  >
                    {s}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </RailCard>
  );
}

export default function ArtifactDetail() {
  const { cls, slug } = useParams<{ cls: string; slug: string }>();
  const [detail, setDetail] = useState<Detail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isClass(cls) || !slug) {
      setError('Invalid artifact reference');
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    getArtifact(cls, slug)
      .then((d) => {
        if (cancelled) return;
        setDetail(d);
        setLoading(false);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to load artifact');
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [cls, slug]);

  if (loading) return <p className="text-sm text-muted">loading…</p>;
  if (error || !detail) {
    return (
      <p className="rounded border border-membrane bg-membrane/10 px-3 py-2 text-sm text-membrane">
        {error ?? 'Not found'}
      </p>
    );
  }

  const { item, body } = detail;
  const aliases = Array.isArray(item.frontmatter.aliases)
    ? (item.frontmatter.aliases as unknown[]).map(String)
    : [];

  return (
    <section className="mx-auto max-w-6xl">
      <p className="font-mono text-xs uppercase tracking-wide text-muted">{item.class}</p>
      <h1 className="mt-1 font-mono text-2xl text-synapse">{item.slug}</h1>
      {item.description && <p className="mt-2 max-w-prose text-muted">{item.description}</p>}
      <div className="mt-3 flex items-center gap-2">
        <LayerBadge layer={item.layer} />
        <StatusChip status={item.status} />
        {item.domain && <span className="font-mono text-xs text-muted">{item.domain}</span>}
      </div>
      <DendriteRule className="mt-4" />

      <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-3">
        <article className="lg:col-span-2">
          <Markdown>{body}</Markdown>
        </article>

        <aside className="space-y-4">
          {aliases.length > 0 && (
            <RailCard title="Aliases">
              <div className="flex flex-wrap gap-1.5">
                {aliases.map((a) => (
                  <span
                    key={a}
                    className="rounded border border-line px-2 py-0.5 font-mono text-xs text-text"
                  >
                    {a}
                  </span>
                ))}
              </div>
            </RailCard>
          )}
          <FrontmatterCard fm={item.frontmatter} />
          {detail.pathwayResolved && <PathwayResolved resolved={detail.pathwayResolved} />}
          <CompanionTree companions={detail.companions} />
          {detail.registryRow && (
            <RailCard title="Registry row">
              <KeyValueList entries={Object.entries(detail.registryRow)} />
            </RailCard>
          )}
          <EvalPanel data={detail.eval} />
        </aside>
      </div>
    </section>
  );
}
