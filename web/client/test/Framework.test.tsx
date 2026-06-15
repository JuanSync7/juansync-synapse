import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { FrameworkData, PipelineData } from '../../shared/types';
import { getFramework, getPipeline } from '../src/api/client';
import Framework from '../src/pages/Framework';

vi.mock('../src/api/client', async () => {
  const actual = await vi.importActual<typeof import('../src/api/client')>('../src/api/client');
  return { ...actual, getFramework: vi.fn(), getPipeline: vi.fn() };
});

const mockFw = vi.mocked(getFramework);
const mockPipe = vi.mocked(getPipeline);

const FRAMEWORK: FrameworkData = {
  groups: {
    skills: [
      {
        slug: 'synapse-router-artifact-creator',
        class: 'skill',
        description: 'Create a new artifact',
        role: null,
      },
    ],
    agents: [],
    protocols: [],
    tools: [],
  },
  lifecycle: [
    { label: 'brainstormer', slug: 'synapse-router-artifact-brainstormer' },
    { label: 'creator', slug: 'synapse-router-artifact-creator' },
    { label: 'suite-validator', slug: null },
  ],
};

const PIPELINE: PipelineData = {
  builtIns: [],
  stages: [
    {
      name: 'docs-spec-writer',
      stage_name: 'spec',
      input_type: 'design_sketch',
      output_type: 'formal_spec',
      requires_all: ['brainstorm'],
      requires_any: [],
      skippable: false,
    },
  ],
  presets: { full: ['brainstorm', 'spec'], bugfix: ['code'] },
};

beforeEach(() => {
  mockFw.mockResolvedValue(FRAMEWORK);
  mockPipe.mockResolvedValue(PIPELINE);
});
afterEach(() => vi.clearAllMocks());

describe('Framework page', () => {
  it('renders the lifecycle strip with links to artifact detail pages', async () => {
    render(
      <MemoryRouter>
        <Framework />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByTestId('lifecycle-creator')).toBeTruthy());
    const creator = screen.getByTestId('lifecycle-creator').closest('a');
    expect(creator?.getAttribute('href')).toBe('/artifact/skill/synapse-router-artifact-creator');
    // a null-slug step renders without a link.
    expect(screen.getByTestId('lifecycle-suite-validator').closest('a')).toBeNull();
  });

  it('renders grouped base artifacts as cards', async () => {
    render(
      <MemoryRouter>
        <Framework />
      </MemoryRouter>,
    );
    await waitFor(() =>
      expect(screen.getAllByText('synapse-router-artifact-creator').length).toBeGreaterThan(0),
    );
  });

  it('renders pipeline stages and preset chips', async () => {
    render(
      <MemoryRouter>
        <Framework />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByTestId('preset-full')).toBeTruthy());
    expect(screen.getByTestId('preset-bugfix')).toBeTruthy();
    expect(screen.getByText('spec')).toBeTruthy();
    expect(screen.getByText(/design_sketch/)).toBeTruthy();
  });
});
