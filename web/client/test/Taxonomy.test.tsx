import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { TaxonomyDetail } from '../../shared/types';
import { getTaxonomy, listTaxonomies, putTaxonomy } from '../src/api/client';
import Taxonomy from '../src/pages/Taxonomy';

vi.mock('../src/api/client', async () => {
  const actual = await vi.importActual<typeof import('../src/api/client')>('../src/api/client');
  return {
    ...actual,
    listTaxonomies: vi.fn(),
    getTaxonomy: vi.fn(),
    putTaxonomy: vi.fn(),
  };
});

const mockList = vi.mocked(listTaxonomies);
const mockGet = vi.mocked(getTaxonomy);
const mockPut = vi.mocked(putTaxonomy);

const DETAIL: TaxonomyDetail = {
  name: 'SKILL_TAXONOMY.md',
  raw: '# Skill Taxonomy\n\nControlled vocabulary for skill slugs.\n',
};

beforeEach(() => {
  mockList.mockResolvedValue({
    files: [
      { name: 'SKILL_TAXONOMY.md', path: 'taxonomy/SKILL_TAXONOMY.md', kind: 'taxonomy' },
      { name: 'SKILL_VOCABULARY.md', path: 'registry/SKILL_VOCABULARY.md', kind: 'vocabulary' },
    ],
  });
  mockGet.mockResolvedValue(DETAIL);
});

afterEach(() => vi.clearAllMocks());

describe('Taxonomy page', () => {
  it('renders the rendered markdown and the vocabulary in the sub-nav', async () => {
    render(
      <MemoryRouter>
        <Taxonomy />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('Skill Taxonomy')).toBeTruthy());
    // Vocabulary file appears in the file list.
    expect(screen.getByText('SKILL_VOCABULARY')).toBeTruthy();
  });

  it('edits and saves, then re-fetches', async () => {
    mockPut.mockResolvedValue(undefined);
    render(
      <MemoryRouter>
        <Taxonomy />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('Skill Taxonomy')).toBeTruthy());

    fireEvent.click(screen.getByText('Edit'));
    const textarea = screen.getByLabelText('Edit taxonomy markdown');
    fireEvent.change(textarea, { target: { value: DETAIL.raw + '\nedited line' } });
    // Dirty indicator surfaces.
    expect(screen.getByText(/unsaved/i)).toBeTruthy();

    fireEvent.click(screen.getByText('Save'));
    await waitFor(() => expect(mockPut).toHaveBeenCalledOnce());
    await waitFor(() => expect(mockGet).toHaveBeenCalledTimes(2));
  });

  it('surfaces a save error inline', async () => {
    mockPut.mockRejectedValue(new Error('disk full'));
    render(
      <MemoryRouter>
        <Taxonomy />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('Skill Taxonomy')).toBeTruthy());

    fireEvent.click(screen.getByText('Edit'));
    fireEvent.change(screen.getByLabelText('Edit taxonomy markdown'), {
      target: { value: DETAIL.raw + '\nx' },
    });
    fireEvent.click(screen.getByText('Save'));
    await waitFor(() => expect(screen.getByText(/disk full/i)).toBeTruthy());
  });
});
