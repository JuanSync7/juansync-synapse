import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { Memo, MemoListResponse } from '../../shared/types';
import { ApiError, getMemo, listMemos, setMemoExecuted } from '../src/api/client';
import Memos from '../src/pages/Memos';

vi.mock('../src/api/client', async () => {
  const actual = await vi.importActual<typeof import('../src/api/client')>('../src/api/client');
  return {
    ...actual,
    listMemos: vi.fn(),
    getMemo: vi.fn(),
    setMemoExecuted: vi.fn(),
  };
});

const mockList = vi.mocked(listMemos);
const mockGet = vi.mocked(getMemo);
const mockSet = vi.mocked(setMemoExecuted);

const PENDING: Memo = {
  id: 'src__skills__a__change_requests__2026-06-10-alpha',
  title: 'Alpha memo',
  source: 'brainstorm:2026-05-31-session',
  session: '2026-05-31-session',
  artifactType: 'skill',
  executed: false,
  executedSource: 'meta',
  path: 'src/skills/a/change_requests/2026-06-10-alpha.md',
  createdDate: '2026-06-10',
};

const DONE: Memo = {
  id: 'src__tools__b__change_requests__2026-06-11-beta',
  title: 'Beta memo',
  source: 'change_requests:src/tools/b/change_requests',
  session: null,
  artifactType: 'tool',
  executed: true,
  executedSource: 'frontmatter',
  path: 'src/tools/b/change_requests/2026-06-11-beta.md',
  createdDate: '2026-06-11',
};

const RESPONSE: MemoListResponse = {
  memos: [PENDING, DONE],
  counts: { total: 2, executed: 1, pending: 1 },
};

beforeEach(() => {
  mockList.mockResolvedValue(RESPONSE);
  mockGet.mockResolvedValue({ memo: PENDING, body: '# Alpha\n\nrendered body' });
});

afterEach(() => vi.clearAllMocks());

describe('Memos page', () => {
  it('renders memos grouped by source with counts', async () => {
    render(
      <MemoryRouter>
        <Memos />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('Alpha memo')).toBeTruthy());
    expect(screen.getByText('Beta memo')).toBeTruthy();
    // Group headings show the source.
    expect(screen.getByText('brainstorm:2026-05-31-session')).toBeTruthy();
    expect(screen.getByText('change_requests:src/tools/b/change_requests')).toBeTruthy();
  });

  it('filters to executed only', async () => {
    render(
      <MemoryRouter>
        <Memos />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('Alpha memo')).toBeTruthy());
    fireEvent.click(screen.getByText('Executed'));
    await waitFor(() => expect(screen.queryByText('Alpha memo')).toBeNull());
    expect(screen.getByText('Beta memo')).toBeTruthy();
  });

  it('toggles a memo (optimistic) and reflects the new state', async () => {
    mockSet.mockResolvedValue({ ...PENDING, executed: true, executedSource: 'frontmatter' });
    render(
      <MemoryRouter>
        <Memos />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('Alpha memo')).toBeTruthy());

    const checkbox = screen.getByLabelText('Mark Alpha memo executed') as HTMLInputElement;
    expect(checkbox.checked).toBe(false);
    fireEvent.click(checkbox);

    await waitFor(() => expect(mockSet).toHaveBeenCalledWith(PENDING.id, true));
    await waitFor(() => {
      const cb = screen.getByLabelText('Mark Alpha memo executed') as HTMLInputElement;
      expect(cb.checked).toBe(true);
    });
  });

  it('reverts and surfaces a PATCH error', async () => {
    mockSet.mockRejectedValue(new ApiError(400, 'Refusing to write a non-memo path'));
    render(
      <MemoryRouter>
        <Memos />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('Alpha memo')).toBeTruthy());

    const checkbox = screen.getByLabelText('Mark Alpha memo executed') as HTMLInputElement;
    fireEvent.click(checkbox);

    await waitFor(() => expect(screen.getByText(/non-memo path/i)).toBeTruthy());
    // Reverted to unchecked.
    const cb = screen.getByLabelText('Mark Alpha memo executed') as HTMLInputElement;
    expect(cb.checked).toBe(false);
  });

  it('opens a detail drawer with the rendered body and a creator-run link (→ /runs?memo=)', async () => {
    render(
      <MemoryRouter>
        <Memos />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('Alpha memo')).toBeTruthy());

    // Click the row title button (inside the list, not the drawer heading).
    fireEvent.click(screen.getAllByText('Alpha memo')[0]!);
    await waitFor(() => expect(screen.getByText('rendered body')).toBeTruthy());

    // The button now links to the creator-run surface, preselected to this memo.
    const runLink = screen.getByText('Run creator with this memo') as HTMLAnchorElement;
    expect(runLink.getAttribute('href')).toBe(`/runs?memo=${encodeURIComponent(PENDING.id)}`);
  });
});
