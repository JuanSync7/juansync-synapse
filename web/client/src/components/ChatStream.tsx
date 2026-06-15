// Transcript renderer for a headless claude session (FR6.3). Takes the parsed
// stream-json events and renders: assistant text as Markdown, tool_use as a
// compact "🔧 tool: <name>" chip with collapsible input, tool_result collapsed,
// and the final result line as a marker. Auto-scrolls to the newest content.
// Wet Lab styling: mono identifiers, synapse-green accents, dendrite divider.
import { useEffect, useRef } from 'react';
import type { SessionEvent } from '../../../shared/types';
import Markdown from './Markdown';

/** A content block inside an assistant/user stream-json message. */
interface Block {
  type?: string;
  text?: string;
  name?: string;
  input?: unknown;
  content?: unknown;
  tool_use_id?: string;
}

/** Pull the content[] blocks out of a stream-json assistant/user line. */
function blocksOf(data: unknown): Block[] {
  if (!data || typeof data !== 'object') return [];
  const msg = (data as { message?: { content?: unknown } }).message;
  const content = msg?.content;
  if (Array.isArray(content)) return content as Block[];
  return [];
}

/** The `result` text from a result line, if present. */
function resultText(data: unknown): string | null {
  if (!data || typeof data !== 'object') return null;
  const r = (data as { result?: unknown }).result;
  return typeof r === 'string' ? r : null;
}

function ToolChip({ name, input }: { name: string; input: unknown }) {
  const pretty = (() => {
    try {
      return JSON.stringify(input, null, 2);
    } catch {
      return String(input);
    }
  })();
  return (
    <details className="my-1 rounded border border-line bg-ink/60 px-2 py-1" data-testid="tool-chip">
      <summary className="cursor-pointer font-mono text-xs text-synapse">
        🔧 tool: <span className="text-text">{name}</span>
      </summary>
      <pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap font-mono text-[0.7rem] text-muted">
        {pretty}
      </pre>
    </details>
  );
}

function ToolResult({ content }: { content: unknown }) {
  const text = typeof content === 'string' ? content : JSON.stringify(content, null, 2);
  return (
    <details className="my-1 rounded border border-line/60 px-2 py-1" data-testid="tool-result">
      <summary className="cursor-pointer font-mono text-[0.7rem] text-muted">↳ tool result</summary>
      <pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap font-mono text-[0.7rem] text-muted">
        {text}
      </pre>
    </details>
  );
}

function EventBlock({ event }: { event: SessionEvent }) {
  if (event.type === 'assistant' || event.type === 'user') {
    const blocks = blocksOf(event.data);
    if (blocks.length === 0) return null;
    return (
      <>
        {blocks.map((b, i) => {
          if (b.type === 'text' && b.text) {
            return (
              <div key={i} className="my-2" data-testid="assistant-text">
                <Markdown>{b.text}</Markdown>
              </div>
            );
          }
          if (b.type === 'tool_use' && b.name) {
            return <ToolChip key={i} name={b.name} input={b.input} />;
          }
          if (b.type === 'tool_result') {
            return <ToolResult key={i} content={b.content} />;
          }
          return null;
        })}
      </>
    );
  }

  if (event.type === 'result') {
    const text = resultText(event.data);
    return (
      <div
        className="my-2 border-t border-line pt-2 font-mono text-xs text-synapse"
        data-testid="result-marker"
      >
        ● session result{text ? `: ${text}` : ''}
      </div>
    );
  }

  if (event.type === 'stderr') {
    const t = (event.data as { text?: string })?.text ?? '';
    if (!t.trim()) return null;
    return (
      <pre className="my-1 whitespace-pre-wrap font-mono text-[0.7rem] text-signal">{t}</pre>
    );
  }

  if (event.type === 'error') {
    const m = (event.data as { message?: string })?.message ?? 'error';
    return (
      <div className="my-1 font-mono text-xs text-membrane" data-testid="error-marker">
        ✕ {m}
      </div>
    );
  }

  // system / exit lines are not rendered as chat content.
  return null;
}

export default function ChatStream({ events }: { events: SessionEvent[] }) {
  const endRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the newest content whenever the transcript grows.
  useEffect(() => {
    // Guarded: jsdom (test env) doesn't implement scrollIntoView.
    endRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'end' });
  }, [events.length]);

  return (
    <div className="space-y-1" data-testid="chat-stream">
      {events.map((event, i) => (
        <EventBlock key={i} event={event} />
      ))}
      <div ref={endRef} />
    </div>
  );
}
