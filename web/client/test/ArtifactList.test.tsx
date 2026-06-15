import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { Artifact, ArtifactListResponse } from '../../shared/types';
import { listArtifacts } from '../src/api/client';
import ArtifactList from '../src/pages/ArtifactList';

vi.mock('../src/api/client', () => ({ listArtifacts: vi.fn() }));
const mockList = vi.mocked(listArtifacts);

function artifact(slug: string, description: string): Artifact {
  return {
    slug,
    class: 'skill',
    layer: 'base',
    path: `synapse/skills/${slug}/SKILL.md`,
    domain: 'code',
    status: 'stable',
    description,
    frontmatter: {},
    hasEval: true,
  };
}

const ALL: Artifact[] = [
  artifact('code-test-writer', 'writes tests'),
  artifact('docs-spec-writer', 'writes specs'),
];

function response(items: Artifact[]): ArtifactListResponse {
  return { items, counts: { skill: 2, agent: 0, protocol: 0, tool: 0, pathway: 0 } };
}

beforeEach(() => {
  // The component re-queries on q change; honor the q filter so the search test works.
  mockList.mockImplementation((params = {}) => {
    const q = params.q?.toLowerCase();
    const items = q
      ? ALL.filter((a) => `${a.slug} ${a.description}`.toLowerCase().includes(q))
      : ALL;
    return Promise.resolve(response(items));
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('ArtifactList', () => {
  it('renders rows from listArtifacts', async () => {
    render(
      <MemoryRouter>
        <ArtifactList cls="skill" />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('code-test-writer')).toBeTruthy());
    expect(screen.getByText('docs-spec-writer')).toBeTruthy();
  });

  it('filters by free-text search (q)', async () => {
    render(
      <MemoryRouter>
        <ArtifactList cls="skill" />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText('code-test-writer')).toBeTruthy());

    fireEvent.change(screen.getByLabelText('Search'), { target: { value: 'spec' } });

    await waitFor(() => expect(screen.queryByText('code-test-writer')).toBeNull());
    expect(screen.getByText('docs-spec-writer')).toBeTruthy();
  });

  it('shows an empty state when there are no artifacts', async () => {
    mockList.mockResolvedValue(response([]));
    render(
      <MemoryRouter>
        <ArtifactList cls="pathway" />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText(/No pathways here yet/i)).toBeTruthy());
  });
});
