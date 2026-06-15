// Scripts control panel (FR8.2, FR8.3). A card grid: one card per shell script
// and per cortex python-CLI command group. Each card shows name (mono),
// audience + action badges, description, and the "where/when to use" prose
// rendered from its docs/cli doc (Markdown, never raw source). The six
// allow-listed read-only commands get a Run button that POSTs to
// /api/scripts/run and shows output in a TerminalPane; everything else is
// labelled documentation-only so it is unambiguous what can execute.
import { useEffect, useState } from 'react';
import type {
  CliCommandMeta,
  ExecResult,
  ScriptMeta,
  ScriptsResponse,
} from '../../../shared/types';
import { ApiError, getScripts, runScript } from '../api/client';
import DendriteRule from '../components/DendriteRule';
import Markdown from '../components/Markdown';
import TerminalPane from '../components/TerminalPane';

// The allow-listed read-only invocations (mirror of safeExec). Maps a command
// name to the (command, args) pair the run endpoint accepts.
const RUNNABLE: Record<string, [string, string[]]> = {
  validate: ['./cortex', ['validate']],
  list: ['./cortex', ['list']],
  available: ['./cortex', ['available']],
  doctor: ['./cortex', ['doctor']],
  pin: ['./cortex', ['pin', 'status']],
  pathway: ['./cortex', ['pathway', 'list']],
};

// Audience badge colors — distinct per DESIGN.md "audience badges on script cards".
const AUDIENCE_STYLE: Record<string, string> = {
  consumer: 'border-synapse text-synapse',
  contributor: 'border-signal text-signal',
  maintainer: 'border-membrane text-membrane',
  automation: 'border-muted text-muted',
};

function Badge({ kind, value }: { kind: string; value: string }) {
  const cls =
    kind === 'audience'
      ? (AUDIENCE_STYLE[value.toLowerCase()] ?? 'border-muted text-muted')
      : 'border-line text-muted';
  return (
    <span
      className={`inline-block rounded-full border px-2 py-0.5 font-mono text-[0.65rem] uppercase tracking-wide ${cls}`}
    >
      {value}
    </span>
  );
}

function RunControl({ name }: { name: string }) {
  const [result, setResult] = useState<ExecResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  const pair = RUNNABLE[name];
  if (!pair) return null;
  const [command, args] = pair;
  const label = `${command} ${args.join(' ')}`.replace('./', '');

  function handleRun() {
    setRunning(true);
    setError(null);
    runScript(command, args)
      .then((r) => {
        setResult(r);
        setRunning(false);
      })
      .catch((e: unknown) => {
        setError(e instanceof ApiError ? e.message : 'Run failed');
        setRunning(false);
      });
  }

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={handleRun}
        disabled={running}
        className="rounded border border-synapse bg-synapse/90 px-3 py-1 font-mono text-xs text-ink hover:bg-synapse disabled:opacity-40"
      >
        {running ? 'Running…' : `Run ${label}`}
      </button>
      {error && (
        <p className="mt-2 rounded border border-membrane bg-membrane/10 px-3 py-2 font-mono text-xs text-membrane">
          {error}
        </p>
      )}
      {result && <TerminalPane result={result} />}
    </div>
  );
}

function ScriptCard({ script }: { script: ScriptMeta }) {
  const runnable = script.name in RUNNABLE;
  return (
    <li className="rounded-lg border border-line bg-surface p-4">
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-sm text-synapse">{script.name}</span>
        <div className="flex shrink-0 flex-wrap items-center gap-1.5">
          {script.audience && <Badge kind="audience" value={script.audience} />}
          {script.action && <Badge kind="action" value={script.action} />}
        </div>
      </div>
      {script.description && <p className="mt-2 text-sm text-muted">{script.description}</p>}
      {script.doc ? (
        <details className="mt-3">
          <summary className="cursor-pointer font-mono text-xs text-muted hover:text-synapse">
            where / when to use
          </summary>
          <div className="mt-2">
            <Markdown>{script.doc}</Markdown>
          </div>
        </details>
      ) : (
        <p className="mt-3 font-mono text-xs text-muted/60">no docs/cli doc</p>
      )}
      {runnable ? (
        <RunControl name={script.name} />
      ) : (
        <p className="mt-3 font-mono text-[0.7rem] uppercase tracking-wide text-muted/60">
          documentation-only
        </p>
      )}
    </li>
  );
}

function CliCommandCard({ command }: { command: CliCommandMeta }) {
  const runnable = command.name in RUNNABLE;
  return (
    <li className="rounded-lg border border-line bg-surface p-4">
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-sm text-synapse">{command.name}</span>
        <Badge kind="kind" value="cli-command" />
      </div>
      <details className="mt-3" open>
        <summary className="cursor-pointer font-mono text-xs text-muted hover:text-synapse">
          where / when to use
        </summary>
        <div className="mt-2">
          <Markdown>{command.doc}</Markdown>
        </div>
      </details>
      {runnable ? (
        <RunControl name={command.name} />
      ) : (
        <p className="mt-3 font-mono text-[0.7rem] uppercase tracking-wide text-muted/60">
          documentation-only
        </p>
      )}
    </li>
  );
}

export default function Scripts() {
  const [data, setData] = useState<ScriptsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getScripts()
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load scripts');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section>
      <h1 className="font-display text-4xl font-light tracking-tight text-text">Scripts</h1>
      <DendriteRule className="mt-3" />
      <p className="mt-4 max-w-2xl text-sm text-muted">
        The cortex command surface. Shell scripts and python-CLI command groups, with their
        documented usage. Read-only commands can be run here; everything else is
        documentation-only.
      </p>

      {error && (
        <p className="mt-6 rounded border border-membrane bg-membrane/10 px-3 py-2 text-sm text-membrane">
          {error}
        </p>
      )}
      {!data && !error && <p className="mt-6 text-sm text-muted">loading…</p>}

      {data && (
        <>
          <h2 className="mt-8 font-mono text-xs uppercase tracking-widest text-muted">scripts</h2>
          <ul className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
            {data.scripts.map((s) => (
              <ScriptCard key={s.name} script={s} />
            ))}
          </ul>

          <h2 className="mt-10 font-mono text-xs uppercase tracking-widest text-muted">
            cli command groups
          </h2>
          <ul className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
            {data.cliCommands.map((c) => (
              <CliCommandCard key={c.name} command={c} />
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
