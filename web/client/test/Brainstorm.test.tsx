import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { SessionListResponse } from '../../shared/types';
import { listSessions, startSession } from '../src/api/client';
import Brainstorm from '../src/pages/Brainstorm';

vi.mock('../src/api/client', async () => {
  const actual = await vi.importActual<typeof import('../src/api/client')>('../src/api/client');
  return {
    ...actual,
    listSessions: vi.fn(),
    startSession: vi.fn(),
    postMessage: vi.fn(),
    getSession: vi.fn(),
    // Keep the real URL helper so the fake EventSource gets the right path.
  };
});

const mockList = vi.mocked(listSessions);
const mockStart = vi.mocked(startSession);

// --- Fake EventSource: capture the instance so the test can push events. -----
class FakeEventSource {
  static last: FakeEventSource | null = null;
  url: string;
  listeners = new Map<string, ((e: MessageEvent) => void)[]>();
  onerror: (() => void) | null = null;
  closed = false;
  constructor(url: string) {
    this.url = url;
    FakeEventSource.last = this;
  }
  addEventListener(type: string, fn: (e: MessageEvent) => void) {
    const arr = this.listeners.get(type) ?? [];
    arr.push(fn);
    this.listeners.set(type, arr);
  }
  emit(type: string, data: unknown) {
    const evt = { data: JSON.stringify(data) } as MessageEvent;
    for (const fn of this.listeners.get(type) ?? []) fn(evt);
  }
  close() {
    this.closed = true;
  }
}

const EMPTY_SESSIONS: SessionListResponse = { sessions: [] };

beforeEach(() => {
  mockList.mockResolvedValue(EMPTY_SESSIONS);
  mockStart.mockResolvedValue({ id: 'sess-1' });
  FakeEventSource.last = null;
  vi.stubGlobal('EventSource', FakeEventSource as unknown as typeof EventSource);
});

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('Brainstorm page', () => {
  it('sends a first message, starts a session, and renders streamed events', async () => {
    render(
      <MemoryRouter>
        <Brainstorm />
      </MemoryRouter>,
    );
    await waitFor(() => expect(mockList).toHaveBeenCalled());

    const textarea = screen.getByLabelText('Message') as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'design a logging skill' } });
    fireEvent.click(screen.getByText('Send'));

    // Started with the brainstormer skill.
    await waitFor(() =>
      expect(mockStart).toHaveBeenCalledWith(
        'design a logging skill',
        'synapse-router-artifact-brainstormer',
      ),
    );

    // The page subscribed to the SSE stream for the new session.
    await waitFor(() => expect(FakeEventSource.last).not.toBeNull());
    const es = FakeEventSource.last!;
    expect(es.url).toContain('/api/sessions/sess-1/events');

    // Push streamed events through the fake EventSource.
    act(() => {
      es.emit('system', { type: 'system', session_id: 's' });
      es.emit('assistant', {
        type: 'assistant',
        message: { role: 'assistant', content: [{ type: 'text', text: 'Here is an idea.' }] },
      });
      es.emit('result', { type: 'result', result: 'Crystallized.' });
    });

    await waitFor(() => expect(screen.getByText('Here is an idea.')).toBeTruthy());
    expect(screen.getByTestId('result-marker').textContent).toContain('Crystallized.');

    // Status flips to done on the result event.
    await waitFor(() =>
      expect(screen.getByTestId('session-status').textContent).toContain('done'),
    );
  });

  it('shows an empty session rail and a New session button', async () => {
    render(
      <MemoryRouter>
        <Brainstorm />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('No past sessions.')).toBeTruthy());
    expect(screen.getByText('+ New session')).toBeTruthy();
    // The memos cross-link is present (FR6.3).
    expect(screen.getByText('View memos →')).toBeTruthy();
  });
});
