// Creator end-to-end run surface (FR7). Reached from the Memos board's "Run
// creator with this memo" button via /runs?memo=<id>, or with a memo picker.
// Shows the target memo + a "Run creator" button; on run it streams the live
// claude session (ChatStream) with a status indicator, then renders a
// verification panel: the validate output in a TerminalPane (green exit 0 /
// membrane-red nonzero), the list of created/changed paths (linking new
// artifacts to their detail page), and a succeeded/failed banner. A runs-history
// rail lists past runs (FR7.3).
//
// Live output arrives over a native EventSource against /api/runs/:id/events;
// after the claude session ends the server sends ONE 'verification' frame
// carrying {createdPaths, validate} which fills the panel without a second
// request. On reload of /runs/:id we GET the run to rehydrate transcript +
// verification.
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import type {
  CreatedPath,
  Memo,
  RunMeta,
  RunStatus,
  RunVerification,
  SessionEvent,
} from '../../../shared/types';
import {
  abortRun,
  getRun,
  listMemos,
  listRuns,
  runEventsUrl,
  startCreatorRun,
} from '../api/client';
import ChatStream from '../components/ChatStream';
import DendriteRule from '../components/DendriteRule';
import TerminalPane from '../components/TerminalPane';

/** A row in the created-paths list: links artifacts to their detail page. */
function CreatedPathRow({ created }: { created: CreatedPath }) {
  return (
    <li className="flex items-center justify-between gap-3 border-b border-line/60 py-1">
      <span className="min-w-0 truncate font-mono text-xs text-text">
        {created.artifact ? (
          <Link
            to={`/artifact/${created.artifact.class}/${created.artifact.slug}`}
            className="text-synapse hover:underline"
          >
            {created.path}
          </Link>
        ) : (
          created.path
        )}
      </span>
      <span className="shrink-0 font-mono text-[0.65rem] uppercase tracking-wide text-muted">
        {created.status}
      </span>
    </li>
  );
}

function VerificationPanel({
  status,
  verification,
}: {
  status: RunStatus;
  verification: RunVerification;
}) {
  const ok = status === 'succeeded';
  return (
    <div className="mt-6" data-testid="verification-panel">
      <div
        className={`rounded-lg border px-4 py-3 font-mono text-sm ${
          ok ? 'border-synapse text-synapse' : 'border-membrane text-membrane'
        }`}
        data-testid="run-banner"
      >
        {ok ? '✓ run succeeded' : '✕ run failed'}
      </div>

      <h2 className="mt-5 font-mono text-xs uppercase tracking-wide text-synapse/80">
        created / changed paths
      </h2>
      {verification.createdPaths.length === 0 ? (
        <p className="mt-1 font-mono text-xs text-muted">No file changes detected.</p>
      ) : (
        <ul className="mt-1 rounded-lg border border-line px-3 py-2">
          {verification.createdPaths.map((c) => (
            <CreatedPathRow key={c.path} created={c} />
          ))}
        </ul>
      )}

      <h2 className="mt-5 font-mono text-xs uppercase tracking-wide text-synapse/80">
        validation
      </h2>
      <TerminalPane result={verification.validate} />
    </div>
  );
}

const STATUS_COLOR: Record<string, string> = {
  running: 'text-synapse',
  succeeded: 'text-synapse',
  failed: 'text-membrane',
  idle: 'text-muted',
};

export default function CreatorRun() {
  const params = useParams();
  const [search] = useSearchParams();
  const navigate = useNavigate();

  const routeRunId = params.id ?? null;
  const memoFromQuery = search.get('memo');

  const [memos, setMemos] = useState<Memo[]>([]);
  const [selectedMemoId, setSelectedMemoId] = useState<string | null>(memoFromQuery);
  const [runs, setRuns] = useState<RunMeta[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(routeRunId);
  const [events, setEvents] = useState<SessionEvent[]>([]);
  const [verification, setVerification] = useState<RunVerification | null>(null);
  const [status, setStatus] = useState<'idle' | RunStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const refreshRuns = useCallback(() => {
    listRuns()
      .then((res) => setRuns(res.runs))
      .catch(() => {
        /* the runs rail is an enhancement; absence is fine */
      });
  }, []);

  useEffect(() => {
    listMemos()
      .then((res) => setMemos(res.memos))
      .catch(() => {
        /* memo picker is an enhancement */
      });
    refreshRuns();
  }, [refreshRuns]);

  const closeStream = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
  }, []);

  useEffect(() => closeStream, [closeStream]);

  /** Subscribe to a run's SSE stream: session events + a verification frame. */
  const subscribe = useCallback(
    (id: string) => {
      closeStream();
      setStatus('running');
      const es = new EventSource(runEventsUrl(id));
      esRef.current = es;

      const handle = (type: SessionEvent['type']) => (e: MessageEvent) => {
        let data: unknown = e.data;
        try {
          data = JSON.parse(e.data);
        } catch {
          /* keep the raw string */
        }
        setEvents((cur) => [...cur, { type, data }]);
      };
      for (const t of ['system', 'assistant', 'user', 'result', 'error', 'stderr'] as const) {
        es.addEventListener(t, handle(t) as EventListener);
      }
      // The terminal verification frame fills the panel + sets final status.
      es.addEventListener('verification', (e) => {
        try {
          setVerification(JSON.parse((e as MessageEvent).data) as RunVerification);
        } catch {
          /* ignore a malformed frame */
        }
      });
      es.addEventListener('exit', (e) => {
        let st: RunStatus = 'failed';
        try {
          const d = JSON.parse((e as MessageEvent).data) as { status?: RunStatus };
          if (d.status) st = d.status;
        } catch {
          /* keep default */
        }
        setStatus(st);
        closeStream();
        refreshRuns();
      });
      es.onerror = () => {
        closeStream();
      };
    },
    [closeStream, refreshRuns],
  );

  /** Open a past/linked run: rehydrate transcript + verification, then stream. */
  const openRun = useCallback(
    (id: string) => {
      setActiveRunId(id);
      setEvents([]);
      setVerification(null);
      setError(null);
      getRun(id)
        .then((detail) => {
          setEvents(detail.events);
          setVerification(detail.verification);
          setStatus(detail.meta.status);
          if (detail.meta.status === 'running') subscribe(id);
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : 'Failed to load run');
        });
    },
    [subscribe],
  );

  // When navigated to /runs/:id, hydrate that run.
  useEffect(() => {
    if (routeRunId) openRun(routeRunId);
    // Only re-run when the route id changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routeRunId]);

  const selectedMemo = useMemo(
    () => memos.find((m) => m.id === selectedMemoId) ?? null,
    [memos, selectedMemoId],
  );

  async function run() {
    if (!selectedMemoId) return;
    setError(null);
    setEvents([]);
    setVerification(null);
    try {
      const { id } = await startCreatorRun(selectedMemoId);
      setActiveRunId(id);
      subscribe(id);
      refreshRuns();
      navigate(`/runs/${id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to start run');
      setStatus('failed');
    }
  }

  async function abort() {
    if (!activeRunId) return;
    try {
      await abortRun(activeRunId);
    } catch {
      /* best effort */
    }
  }

  const statusColor = STATUS_COLOR[status] ?? 'text-muted';

  return (
    <section>
      <div className="flex items-baseline justify-between">
        <h1 className="font-display text-4xl font-light tracking-tight text-text">Creator Run</h1>
        <Link to="/memos" className="font-mono text-xs text-synapse hover:underline">
          ← Memos
        </Link>
      </div>
      <DendriteRule className="mt-3" />

      <div className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-[14rem_1fr]">
        {/* Runs history rail */}
        <aside aria-label="Runs">
          <h2 className="mb-2 font-mono text-xs uppercase tracking-wide text-synapse/80">history</h2>
          <ul className="space-y-1">
            {runs.length === 0 && <li className="font-mono text-xs text-muted">No past runs.</li>}
            {runs.map((r) => (
              <li key={r.id}>
                <button
                  type="button"
                  onClick={() => {
                    navigate(`/runs/${r.id}`);
                    openRun(r.id);
                  }}
                  className={`block w-full truncate rounded px-2 py-1 text-left font-mono text-xs hover:text-synapse ${
                    r.id === activeRunId ? 'bg-surface text-synapse' : 'text-muted'
                  }`}
                  title={r.memoPath}
                >
                  {r.memoId}
                  <span
                    className={`ml-1 text-[0.65rem] ${
                      r.status === 'failed' ? 'text-membrane' : 'text-muted/70'
                    }`}
                  >
                    {r.status}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        {/* Run target + stream + verification */}
        <div className="lg:border-l lg:border-line lg:pl-8">
          {/* Memo picker (when no memo preselected) */}
          {!selectedMemoId && (
            <div className="mb-4">
              <label
                htmlFor="memo-picker"
                className="mb-1 block font-mono text-xs uppercase tracking-wide text-muted"
              >
                pick a memo
              </label>
              <select
                id="memo-picker"
                aria-label="Pick a memo"
                value=""
                onChange={(e) => setSelectedMemoId(e.target.value || null)}
                className="w-full rounded border border-line bg-ink px-3 py-2 font-mono text-sm text-text outline-none focus:border-synapse"
              >
                <option value="">— select —</option>
                {memos.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.title}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="rounded-lg border border-line bg-surface p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <span className="block font-mono text-xs uppercase tracking-wide text-muted">
                  target memo
                </span>
                <span
                  className="block truncate font-mono text-sm text-text"
                  data-testid="target-memo"
                >
                  {selectedMemo ? selectedMemo.title : selectedMemoId ?? 'no memo selected'}
                </span>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <span className={`font-mono text-xs ${statusColor}`} data-testid="run-status">
                  ● {status}
                </span>
                {status === 'running' ? (
                  <button
                    type="button"
                    onClick={() => void abort()}
                    className="rounded border border-membrane px-3 py-1 font-mono text-xs text-membrane hover:bg-membrane/10"
                  >
                    Abort
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => void run()}
                    disabled={!selectedMemoId}
                    className="rounded border border-synapse px-4 py-1.5 font-mono text-xs text-synapse hover:bg-synapse/10 disabled:opacity-40"
                  >
                    Run creator
                  </button>
                )}
              </div>
            </div>
          </div>

          {error && (
            <p className="mt-3 rounded border border-membrane bg-membrane/10 px-3 py-2 font-mono text-xs text-membrane">
              {error}
            </p>
          )}

          {(events.length > 0 || status === 'running') && (
            <div
              className="mt-4 min-h-[12rem] rounded-lg border border-line bg-surface p-4"
              data-testid="transcript"
            >
              {events.length === 0 ? (
                <p className="font-mono text-xs text-muted">Starting the creator run…</p>
              ) : (
                <ChatStream events={events} />
              )}
            </div>
          )}

          {verification && status !== 'running' && status !== 'idle' && (
            <VerificationPanel status={status} verification={verification} />
          )}
        </div>
      </div>
    </section>
  );
}
