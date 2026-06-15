// Headless brainstorm chat (FR6.3). Left rail: persisted session list + "New
// session" (resume a past session by clicking it). Center: the streamed
// transcript (ChatStream) + an input box. The first message POSTs /api/sessions
// (skill = synapse-router-artifact-brainstormer) and starts a session; later
// messages POST /messages to resume. Live output arrives over a native
// EventSource against /:id/events; the same stream is re-subscribed after each
// turn so resumed output flows in. On reload with a session id we GET the
// session to rehydrate the transcript (FR6.4).
//
// Memos created during a session land in .brainstorms/ → a "View memos" link to
// /memos lets the user jump to the board (which crawls fresh on load).
import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import type { SessionEvent, SessionMeta } from '../../../shared/types';
import {
  getSession,
  listSessions,
  postMessage,
  sessionEventsUrl,
  startSession,
} from '../api/client';
import ChatStream from '../components/ChatStream';
import DendriteRule from '../components/DendriteRule';

const SKILL = 'synapse-router-artifact-brainstormer';

export default function Brainstorm() {
  const [sessions, setSessions] = useState<SessionMeta[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [events, setEvents] = useState<SessionEvent[]>([]);
  const [status, setStatus] = useState<'idle' | 'running' | 'done' | 'error'>('idle');
  const [input, setInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const refreshSessions = useCallback(() => {
    listSessions()
      .then((res) => setSessions(res.sessions))
      .catch(() => {
        /* the session rail is an enhancement; absence is fine */
      });
  }, []);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  // Tear down any open EventSource when unmounting or switching sessions.
  const closeStream = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
  }, []);

  useEffect(() => closeStream, [closeStream]);

  /** Subscribe to the SSE stream for a session id, appending live events. */
  const subscribe = useCallback(
    (id: string) => {
      closeStream();
      setStatus('running');
      const es = new EventSource(sessionEventsUrl(id));
      esRef.current = es;

      const handle = (type: SessionEvent['type']) => (e: MessageEvent) => {
        let data: unknown = e.data;
        try {
          data = JSON.parse(e.data);
        } catch {
          /* keep the raw string */
        }
        setEvents((cur) => [...cur, { type, data }]);
        if (type === 'result') setStatus('done');
        if (type === 'error') setStatus('error');
        if (type === 'exit') {
          setStatus((s) => (s === 'running' ? 'done' : s));
          closeStream();
          // Memos may have been written during the run — refresh the rail.
          refreshSessions();
        }
      };

      for (const t of ['system', 'assistant', 'user', 'result', 'error', 'stderr', 'exit'] as const) {
        es.addEventListener(t, handle(t) as EventListener);
      }
      es.onerror = () => {
        // EventSource auto-reconnects; once the server has ended the stream we
        // simply stop. Don't surface transient reconnect noise as an error.
        closeStream();
      };
    },
    [closeStream, refreshSessions],
  );

  /** Open a past session: rehydrate its transcript, then live-subscribe. */
  const openSession = useCallback(
    (id: string) => {
      setActiveId(id);
      setEvents([]);
      setError(null);
      getSession(id)
        .then((detail) => {
          setEvents(detail.events);
          setStatus(detail.meta.status);
          if (detail.meta.status === 'running') subscribe(id);
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : 'Failed to load session');
        });
    },
    [subscribe],
  );

  function newSession() {
    closeStream();
    setActiveId(null);
    setEvents([]);
    setStatus('idle');
    setError(null);
    setInput('');
  }

  async function send() {
    const message = input.trim();
    if (!message) return;
    setInput('');
    setError(null);
    try {
      if (activeId === null) {
        const { id } = await startSession(message, SKILL);
        setActiveId(id);
        subscribe(id);
        refreshSessions();
      } else {
        await postMessage(activeId, message);
        subscribe(activeId);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      setStatus('error');
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends; Shift+Enter inserts a newline.
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  }

  const statusColor =
    status === 'running'
      ? 'text-synapse'
      : status === 'error'
        ? 'text-membrane'
        : status === 'done'
          ? 'text-muted'
          : 'text-muted';

  return (
    <section>
      <div className="flex items-baseline justify-between">
        <h1 className="font-display text-4xl font-light tracking-tight text-text">Brainstorm</h1>
        <Link to="/memos" className="font-mono text-xs text-synapse hover:underline">
          View memos →
        </Link>
      </div>
      <DendriteRule className="mt-3" />

      <div className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-[14rem_1fr]">
        {/* Session rail */}
        <aside aria-label="Sessions">
          <button
            type="button"
            onClick={newSession}
            className="mb-3 w-full rounded border border-synapse px-3 py-1.5 font-mono text-xs text-synapse hover:bg-synapse/10"
          >
            + New session
          </button>
          <ul className="space-y-1">
            {sessions.length === 0 && (
              <li className="font-mono text-xs text-muted">No past sessions.</li>
            )}
            {sessions.map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  onClick={() => openSession(s.id)}
                  className={`block w-full truncate rounded px-2 py-1 text-left font-mono text-xs hover:text-synapse ${
                    s.id === activeId ? 'bg-surface text-synapse' : 'text-muted'
                  }`}
                  title={s.title}
                >
                  {s.title}
                  <span className="ml-1 text-[0.65rem] text-muted/70">{s.status}</span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        {/* Transcript + input */}
        <div className="lg:border-l lg:border-line lg:pl-8">
          <div className="mb-2 flex items-center gap-2 font-mono text-xs">
            <span className={statusColor} data-testid="session-status">
              ● {status}
            </span>
          </div>

          <div
            className="min-h-[18rem] rounded-lg border border-line bg-surface p-4"
            data-testid="transcript"
          >
            {events.length === 0 ? (
              <p className="font-mono text-xs text-muted">
                Describe the artifact you want to explore. Your first message starts a brainstorm
                session.
              </p>
            ) : (
              <ChatStream events={events} />
            )}
          </div>

          {error && (
            <p className="mt-3 rounded border border-membrane bg-membrane/10 px-3 py-2 font-mono text-xs text-membrane">
              {error}
            </p>
          )}

          <div className="mt-3 flex items-end gap-2">
            <textarea
              aria-label="Message"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              rows={3}
              placeholder="Message claude…"
              className="flex-1 resize-y rounded border border-line bg-ink px-3 py-2 font-mono text-sm text-text outline-none focus:border-synapse"
            />
            <button
              type="button"
              onClick={() => void send()}
              disabled={!input.trim()}
              className="rounded border border-synapse px-4 py-2 font-mono text-xs text-synapse hover:bg-synapse/10 disabled:opacity-40"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
