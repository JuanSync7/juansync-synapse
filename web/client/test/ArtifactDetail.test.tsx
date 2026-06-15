import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import type { ArtifactDetail as Detail } from '../../shared/types';
import { getArtifact } from '../src/api/client';
import ArtifactDetail from '../src/pages/ArtifactDetail';

vi.mock('../src/api/client', () => ({ getArtifact: vi.fn() }));
const mockGet = vi.mocked(getArtifact);

const detail: Detail = {
  item: {
    slug: 'code-test-writer',
    class: 'skill',
    layer: 'base',
    path: 'synapse/skills/code-test-writer/SKILL.md',
    domain: 'code',
    status: 'stable',
    description: 'writes tests',
    frontmatter: { name: 'code-test-writer', role: 'writer' },
    hasEval: true,
  },
  body: '# How it works\n\nThis skill writes **tests**.',
  eval: {
    raw: '...',
    isPlaceholder: false,
    groups: {
      execution: [{ id: 'EVAL-E01', text: 'runs clean', checked: true }],
      output: [],
      other: [],
    },
  },
  companions: [
    { name: 'guide.md', path: 'synapse/skills/code-test-writer/references/guide.md', kind: 'reference' },
  ],
  registryRow: null,
  pathwayResolved: null,
};

beforeEach(() => {
  mockGet.mockResolvedValue(detail);
});
afterEach(() => {
  vi.clearAllMocks();
});

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/artifact/:cls/:slug" element={<ArtifactDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ArtifactDetail', () => {
  it('renders body, frontmatter and eval panel', async () => {
    renderAt('/artifact/skill/code-test-writer');

    await waitFor(() =>
      expect(screen.getByRole('heading', { name: 'How it works' })).toBeTruthy(),
    );
    // frontmatter card key/value
    expect(screen.getByText('role')).toBeTruthy();
    // eval panel group + criterion
    expect(screen.getByText('Execution')).toBeTruthy();
    expect(screen.getByText('EVAL-E01')).toBeTruthy();
    // companion file name
    expect(screen.getByText('guide.md')).toBeTruthy();
  });
});
