import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { SessionEvent } from '../../shared/types';
import ChatStream from '../src/components/ChatStream';

const EVENTS: SessionEvent[] = [
  { type: 'system', data: { type: 'system', subtype: 'init', session_id: 's1' } },
  {
    type: 'assistant',
    data: {
      type: 'assistant',
      message: { role: 'assistant', content: [{ type: 'text', text: 'Let us explore the idea.' }] },
    },
  },
  {
    type: 'assistant',
    data: {
      type: 'assistant',
      message: {
        role: 'assistant',
        content: [{ type: 'tool_use', id: 't1', name: 'Read', input: { file_path: '/x' } }],
      },
    },
  },
  {
    type: 'user',
    data: {
      type: 'user',
      message: {
        role: 'user',
        content: [{ type: 'tool_result', tool_use_id: 't1', content: 'the file body' }],
      },
    },
  },
  { type: 'result', data: { type: 'result', result: 'Crystallized a memo.' } },
];

describe('ChatStream', () => {
  it('renders assistant text, a tool chip, tool result, and the result marker', () => {
    render(<ChatStream events={EVENTS} />);

    // Assistant text (Markdown rendered).
    expect(screen.getByText('Let us explore the idea.')).toBeTruthy();

    // Tool chip shows "🔧 tool: <name>".
    const chip = screen.getByTestId('tool-chip');
    expect(chip.textContent).toContain('Read');
    expect(chip.textContent).toContain('🔧 tool:');

    // Tool result block present.
    expect(screen.getByTestId('tool-result')).toBeTruthy();

    // Final result marker.
    const marker = screen.getByTestId('result-marker');
    expect(marker.textContent).toContain('Crystallized a memo.');
  });

  it('ignores system/exit lines (no crash, no chat block)', () => {
    render(
      <ChatStream
        events={[
          { type: 'system', data: { type: 'system', session_id: 's1' } },
          { type: 'exit', data: { code: 0 } },
        ]}
      />,
    );
    expect(screen.getByTestId('chat-stream')).toBeTruthy();
    expect(screen.queryByTestId('assistant-text')).toBeNull();
  });
});
