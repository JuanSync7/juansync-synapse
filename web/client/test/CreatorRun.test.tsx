import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { Memo, MemoListResponse, RunListResponse } from '../../shared/types';
import { listMemos, listRuns, startCreatorRun } from '../src/api/client';
import CreatorRun from '../src/pages/CreatorRun';

vi.mock('../src/api/client', async () => {
  const actual = await vi.importActual<typeof import('../src/api/client')>('../src/api/client');
  return {
    ...actual,
    listMemos: vi.fn(),
    listRuns: vi.fn(),
    startCreatorRun: vi.fn(),
    getRun: vi.fn(),
    abortRun: vi.fn(),
    // Keep the real runEventsUrl helper.
  };
});

const mockMemos = vi.mocked(listMemos);
const mockRuns = vi.mocked(listRuns);
const mockStart = vi.mocked(startCreatorRun);

// --- Fake EventSource (S8 technique): capture the instance to push events. ---
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

const MEMO: Memo = {
  id: 'src__skills__demo__change_requests__2026-06-13-demo',
  title: 'Demo memo',
  source: 'change_requests:src/skills/demo/change_requests',
  session: null,
  artifactType: 'skill',
  executed: false,
  executedSource: 'default',
  path: 'src/skills/demo/change_requests/2026-06-13-demo.md',
  createdDate: '2026-06-13',
};

const MEMOS: MemoListResponse = {
  memos: [MEMO],
  counts: { total: 1, executed: 0, pending: 1 },
};
const NO_RUNS: RunListResponse = { runs: [] };

beforeEach(() => {
  mockMemos.mockResolvedValue(MEMOS);
  mockRuns.mockResolvedValue(NO_RUNS);
  mockStart.mockResolvedValue({ id: 'run-1' });
  FakeEventSource.last = null;
  vi.stubGlobal('EventSource', FakeEventSource as unknown as typeof EventSource);
});

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe('CreatorRun page', () => {
  it('shows the preselected memo (?memo=) and a run button', async () => {
    render(
      <MemoryRouter initialEntries={[`/runs?memo=${MEMO.id}`]}>
        <CreatorRun />
      </MemoryRouter>,
    );
    await waitFor(() => expect(mockMemos).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByTestId('target-memo').textContent).toContain('Demo memo'));
    expect(screen.getByText('Run creator')).toBeTruthy();
  });

  it('starts a run, streams events, and renders the verification panel', async () => {
    render(
      <MemoryRouter initialEntries={[`/runs?memo=${MEMO.id}`]}>
        <CreatorRun />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByTestId('target-memo').textContent).toContain('Demo memo'));

    fireEvent.click(screen.getByText('Run creator'));
    await waitFor(() => expect(mockStart).toHaveBeenCalledWith(MEMO.id));

    await waitFor(() => expect(FakeEventSource.last).not.toBeNull());
    const es = FakeEventSource.last!;
    expect(es.url).toContain('/api/runs/run-1/events');

    // Stream session events.
    act(() => {
      es.emit('assistant', {
        type: 'assistant',
        message: { role: 'assistant', content: [{ type: 'text', text: 'Scaffolding the skill.' }] },
      });
      es.emit('result', { type: 'result', result: 'Created src/skills/demo/demo-skill/SKILL.md' });
    });
    await waitFor(() => expect(screen.getByText('Scaffolding the skill.')).toBeTruthy());

    // The terminal verification frame fills the panel; exit sets final status.
    act(() => {
      es.emit('verification', {
        createdPaths: [
          {
            path: 'src/skills/demo/demo-skill/SKILL.md',
            status: '??',
            artifact: { class: 'skill', slug: 'demo-skill' },
          },
        ],
        validate: { command: './cortex validate', stdout: '0 errors / 0 warnings', stderr: '', exitCode: 0 },
      });
      es.emit('exit', { status: 'succeeded' });
    });

    await waitFor(() => expect(screen.getByTestId('verification-panel')).toBeTruthy());
    // Succeeded banner.
    expect(screen.getByTestId('run-banner').textContent).toContain('succeeded');
    // Validate output in a TerminalPane with exit 0 (green).
    expect(screen.getByTestId('exit-badge').textContent).toContain('exit 0');
    expect(screen.getByText('0 errors / 0 warnings')).toBeTruthy();
    // Created path links to the new artifact's detail page.
    const link = screen.getByText('src/skills/demo/demo-skill/SKILL.md') as HTMLAnchorElement;
    expect(link.getAttribute('href')).toBe('/artifact/skill/demo-skill');
  });

  it('renders a membrane-red failed banner on a nonzero validate', async () => {
    render(
      <MemoryRouter initialEntries={[`/runs?memo=${MEMO.id}`]}>
        <CreatorRun />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByTestId('target-memo').textContent).toContain('Demo memo'));
    fireEvent.click(screen.getByText('Run creator'));
    await waitFor(() => expect(FakeEventSource.last).not.toBeNull());
    const es = FakeEventSource.last!;

    act(() => {
      es.emit('verification', {
        createdPaths: [],
        validate: { command: './cortex validate', stdout: '', stderr: '1 error', exitCode: 1 },
      });
      es.emit('exit', { status: 'failed' });
    });

    await waitFor(() => expect(screen.getByTestId('run-banner').textContent).toContain('failed'));
    expect(screen.getByTestId('exit-badge').textContent).toContain('exit 1');
  });
});
