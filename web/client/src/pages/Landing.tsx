// Landing surface (FR9): a clean hero wordmark, the three-layer packaging
// explanation, live per-class counts from the crawler, and links to the GitHub
// repo + docs. Minimalist redesign — no dendrite field, no serif display.
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import type { ArtifactClass, Counts } from '../../../shared/types';
import { listArtifacts } from '../api/client';

const REPO_URL = 'https://github.com/JuanSync7/ai-synapse';

const CLASSES: { cls: ArtifactClass; route: string; label: string }[] = [
  { cls: 'skill', route: '/skills', label: 'skills' },
  { cls: 'agent', route: '/agents', label: 'agents' },
  { cls: 'protocol', route: '/protocols', label: 'protocols' },
  { cls: 'tool', route: '/tools', label: 'tools' },
  { cls: 'pathway', route: '/pathways', label: 'pathways' },
];

export default function Landing() {
  const [counts, setCounts] = useState<Counts | null>(null);

  useEffect(() => {
    let cancelled = false;
    listArtifacts()
      .then((res) => {
        if (!cancelled) setCounts(res.counts);
      })
      .catch(() => {
        // Counts are decorative on the landing; failure leaves them dashed.
        if (!cancelled) setCounts(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="mx-auto max-w-5xl">
      <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-muted">
        <span className="h-1.5 w-1.5 rounded-full bg-synapse" />
        Living artifact library
      </span>

      <h1 className="mt-5 text-5xl font-semibold leading-tight tracking-tight text-text md:text-6xl">
        Synapse
      </h1>
      <p className="mt-5 max-w-2xl text-lg leading-relaxed text-muted">
        A library of composable artifacts — skills, agents, protocols, tools and pathways — for
        Claude Code and other AI coding harnesses. The framework ships in three layers: a{' '}
        <span className="font-medium text-synapse">base</span> (ai-synapse: the meta-tools that
        build and govern artifacts), an <span className="font-medium text-signal">add-on</span>{' '}
        overlay (juansync-synapse: the adopter&rsquo;s own synapses in{' '}
        <code className="rounded bg-surface px-1 py-0.5 font-mono text-sm text-text">src/</code>),
        and <span className="font-medium text-text">external</span> suites wired in as submodules.
        Everything below is crawled from the repo at runtime — nothing is hardcoded.
      </p>

      <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-5">
        {CLASSES.map(({ cls, route, label }) => (
          <Link
            key={cls}
            to={route}
            className="group rounded-xl border border-line bg-surface px-4 py-6 text-center shadow-sm transition-all hover:-translate-y-0.5 hover:border-synapse/40 hover:shadow"
          >
            <div
              className="text-4xl font-semibold tracking-tight text-text"
              data-testid={`count-${cls}`}
            >
              {counts ? counts[cls] : '—'}
            </div>
            <div className="mt-1.5 text-xs font-medium uppercase tracking-wide text-muted group-hover:text-synapse">
              {label}
            </div>
          </Link>
        ))}
      </div>

      <div className="mt-10 flex flex-wrap gap-5 text-sm font-medium">
        <a
          href={REPO_URL}
          target="_blank"
          rel="noreferrer"
          className="text-synapse hover:underline"
        >
          GitHub repo →
        </a>
        <Link to="/framework" className="text-synapse hover:underline">
          Framework &amp; pipeline →
        </Link>
        <Link to="/skills" className="text-synapse hover:underline">
          Browse skills →
        </Link>
      </div>
    </section>
  );
}
