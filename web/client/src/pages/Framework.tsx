// Framework page (FR4) — the synapse/ meta-tool layer, kept SEPARATE from the
// adopter artifact browse pages. Four parts: an intro explaining what the
// framework layer is; a lifecycle strip showing the creation pipeline order as
// connected dendrite nodes (each linking to its artifact detail page); the base
// artifacts grouped by class as cards; and the pipeline view rendered from
// /api/pipeline (stages with input→output types, requires_* edges, and the
// named presets as chips).
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import type {
  FrameworkArtifact,
  FrameworkData,
  LifecycleStep,
  PipelineData,
} from '../../../shared/types';
import { getFramework, getPipeline } from '../api/client';
import DendriteRule from '../components/DendriteRule';

function LifecycleStrip({ steps }: { steps: LifecycleStep[] }) {
  return (
    <ol className="flex flex-wrap items-center gap-x-1 gap-y-3" aria-label="Creation lifecycle">
      {steps.map((step, i) => {
        const node = (
          <span
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 font-mono text-xs ${
              step.slug
                ? 'border-synapse/60 text-synapse hover:bg-synapse/10'
                : 'border-line text-muted'
            }`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-synapse" aria-hidden="true" />
            {step.label}
          </span>
        );
        return (
          <li key={step.label} className="flex items-center">
            {step.slug ? (
              <Link to={`/artifact/skill/${step.slug}`} data-testid={`lifecycle-${step.label}`}>
                {node}
              </Link>
            ) : (
              <span data-testid={`lifecycle-${step.label}`}>{node}</span>
            )}
            {i < steps.length - 1 && (
              <span className="mx-1 text-synapse/50" aria-hidden="true">
                →
              </span>
            )}
          </li>
        );
      })}
    </ol>
  );
}

function ArtifactGroup({ title, items }: { title: string; items: FrameworkArtifact[] }) {
  if (items.length === 0) return null;
  return (
    <div className="mt-6">
      <h3 className="font-mono text-xs uppercase tracking-widest text-muted">{title}</h3>
      <ul className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
        {items.map((a) => (
          <li key={a.slug}>
            <Link
              to={`/artifact/${a.class}/${a.slug}`}
              className="group block rounded-lg border border-line bg-surface px-4 py-3 transition-colors hover:border-synapse/60"
            >
              <span className="font-mono text-sm text-synapse group-hover:underline">{a.slug}</span>
              {a.description && <p className="mt-1.5 line-clamp-2 text-sm text-muted">{a.description}</p>}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function PipelineView({ pipeline }: { pipeline: PipelineData }) {
  return (
    <div className="mt-4">
      {Object.keys(pipeline.presets).length > 0 && (
        <div className="mb-5 flex flex-wrap items-center gap-2">
          <span className="font-mono text-xs uppercase tracking-widest text-muted">presets</span>
          {Object.entries(pipeline.presets).map(([name, stages]) => (
            <span
              key={name}
              title={stages.join(' → ')}
              className="rounded-full border border-signal/60 px-3 py-0.5 font-mono text-xs text-signal"
              data-testid={`preset-${name}`}
            >
              {name}
            </span>
          ))}
        </div>
      )}
      <ul className="space-y-2">
        {pipeline.stages.map((s) => (
          <li
            key={s.name}
            className="rounded-lg border border-line bg-surface px-4 py-3 font-mono text-xs"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-synapse">{s.stage_name || s.name}</span>
              <span className="text-muted">
                {s.input_type ?? '—'} <span className="text-synapse/60">→</span>{' '}
                {s.output_type ?? '—'}
              </span>
            </div>
            {(s.requires_all.length > 0 || s.requires_any.length > 0) && (
              <p className="mt-1.5 text-muted/70">
                {s.requires_all.length > 0 && <>requires all: {s.requires_all.join(', ')} </>}
                {s.requires_any.length > 0 && <>requires any: {s.requires_any.join(', ')}</>}
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function Framework() {
  const [framework, setFramework] = useState<FrameworkData | null>(null);
  const [pipeline, setPipeline] = useState<PipelineData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getFramework(), getPipeline()])
      .then(([f, p]) => {
        if (cancelled) return;
        setFramework(f);
        setPipeline(p);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load framework');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section>
      <h1 className="font-display text-4xl font-light tracking-tight text-text">Framework</h1>
      <DendriteRule className="mt-3" />
      <p className="mt-4 max-w-2xl text-sm text-muted">
        The <span className="text-synapse">synapse/</span> layer is the framework itself — the
        meta-tools that build, evaluate, and govern every other artifact. These are not adopter
        skills; they are the machinery that produces and certifies them.
      </p>

      {error && (
        <p className="mt-6 rounded border border-membrane bg-membrane/10 px-3 py-2 text-sm text-membrane">
          {error}
        </p>
      )}
      {!framework && !error && <p className="mt-6 text-sm text-muted">loading…</p>}

      {framework && (
        <>
          <div className="mt-8">
            <h2 className="font-mono text-xs uppercase tracking-widest text-muted">
              creation lifecycle
            </h2>
            <div className="mt-3">
              <LifecycleStrip steps={framework.lifecycle} />
            </div>
          </div>

          <div className="mt-10">
            <h2 className="font-display text-2xl font-light text-text">Base artifacts</h2>
            <DendriteRule className="mt-2" pulse={false} />
            <ArtifactGroup title="skills" items={framework.groups.skills} />
            <ArtifactGroup title="agents" items={framework.groups.agents} />
            <ArtifactGroup title="protocols" items={framework.groups.protocols} />
            <ArtifactGroup title="tools" items={framework.groups.tools} />
          </div>
        </>
      )}

      {pipeline && (
        <div className="mt-10">
          <h2 className="font-display text-2xl font-light text-text">Pipeline</h2>
          <DendriteRule className="mt-2" pulse={false} />
          <PipelineView pipeline={pipeline} />
        </div>
      )}
    </section>
  );
}
