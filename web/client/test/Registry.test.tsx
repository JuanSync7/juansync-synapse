import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { RegistryDetail } from '../../shared/types';
import { ApiError, getRegistry, listRegistries, putRegistry } from '../src/api/client';
import Registry from '../src/pages/Registry';

vi.mock('../src/api/client', async () => {
  const actual = await vi.importActual<typeof import('../src/api/client')>('../src/api/client');
  return {
    ...actual,
    listRegistries: vi.fn(),
    getRegistry: vi.fn(),
    putRegistry: vi.fn(),
  };
});

const mockList = vi.mocked(listRegistries);
const mockGet = vi.mocked(getRegistry);
const mockPut = vi.mocked(putRegistry);

const DETAIL: RegistryDetail = {
  name: 'SKILL_REGISTRY.md',
  raw: '# Skills Registry\n\n| Skill | Status |\n|---|---|\n| [code-test-writer](p) | stable |\n',
  table: {
    headers: ['Skill', 'Status'],
    rows: [['[code-test-writer](p)', 'stable']],
  },
};

beforeEach(() => {
  mockList.mockResolvedValue({
    files: [{ name: 'SKILL_REGISTRY.md', path: 'registry/SKILL_REGISTRY.md', kind: 'registry' }],
  });
  mockGet.mockResolvedValue(DETAIL);
});

afterEach(() => vi.clearAllMocks());

describe('Registry page', () => {
  it('renders the parsed table with a cross-linked slug and status chip', async () => {
    render(
      <MemoryRouter>
        <Registry />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('code-test-writer')).toBeTruthy());
    // First-column slug cross-links to the artifact page.
    const link = screen.getByText('code-test-writer').closest('a');
    expect(link?.getAttribute('href')).toBe('/artifact/skill/code-test-writer');
    // Status chip rendered (StatusChip uppercases the text).
    expect(screen.getByText('stable')).toBeTruthy();
  });

  it('enters edit mode and surfaces a 422 shape-mismatch error', async () => {
    mockPut.mockRejectedValue(new ApiError(422, 'Edit rejected: the table must keep the same columns'));
    render(
      <MemoryRouter>
        <Registry />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('code-test-writer')).toBeTruthy());

    fireEvent.click(screen.getByText('Edit'));
    const textarea = screen.getByLabelText('Edit registry markdown') as HTMLTextAreaElement;
    expect(textarea).toBeTruthy();

    fireEvent.change(textarea, { target: { value: DETAIL.raw + '\nmutated' } });
    fireEvent.click(screen.getByText('Save'));

    await waitFor(() =>
      expect(screen.getByText(/the table must keep the same columns/i)).toBeTruthy(),
    );
  });

  it('saves a valid edit and re-fetches', async () => {
    mockPut.mockResolvedValue(undefined);
    render(
      <MemoryRouter>
        <Registry />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('code-test-writer')).toBeTruthy());

    fireEvent.click(screen.getByText('Edit'));
    const textarea = screen.getByLabelText('Edit registry markdown');
    fireEvent.change(textarea, { target: { value: DETAIL.raw + '\nmore' } });
    fireEvent.click(screen.getByText('Save'));

    await waitFor(() => expect(mockPut).toHaveBeenCalledOnce());
    // re-fetch after save: getRegistry called again (initial load + re-fetch).
    await waitFor(() => expect(mockGet).toHaveBeenCalledTimes(2));
  });
});
