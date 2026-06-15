// Mono output panel for command runs (FR8.3). A dark code surface (kept dark on
// the light UI for contrast/readability, like docs code blocks), whitespace
// preserved, with an exit-code badge: violet for 0, red for nonzero. stderr is
// appended below stdout, dimmed. See DESIGN.md "terminal panes" — kept subtle
// (a single fade-rise on mount).
import type { ExecResult } from '../../../shared/types';

export default function TerminalPane({ result }: { result: ExecResult }) {
  const ok = result.exitCode === 0;
  return (
    <div
      className="fade-rise mt-3 overflow-hidden rounded-xl border border-code bg-code shadow-sm"
      data-testid="terminal-pane"
    >
      <div className="flex items-center justify-between border-b border-white/10 px-3 py-1.5">
        <span className="font-mono text-xs text-white/50">$ {result.command}</span>
        <span
          className={`rounded-md border px-2 py-0.5 font-mono text-[0.7rem] uppercase tracking-wide ${
            ok ? 'border-synapse/60 text-synapse' : 'border-membrane/60 text-membrane'
          }`}
          data-testid="exit-badge"
        >
          exit {result.exitCode}
        </span>
      </div>
      <pre className="max-h-96 overflow-auto whitespace-pre-wrap px-3 py-2 font-mono text-xs text-[#e6e8ec]">
        {result.stdout}
        {result.stderr && (
          <span className="text-white/45">
            {result.stdout ? '\n' : ''}
            {result.stderr}
          </span>
        )}
      </pre>
    </div>
  );
}
