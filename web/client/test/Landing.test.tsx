import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { ArtifactListResponse } from '../../shared/types';

// Landing fetches counts through the real client, so we mock fetch itself here
// to exercise the wrapper end-to-end.
const payload: ArtifactListResponse = {
  items: [],
  counts: { skill: 37, agent: 34, protocol: 9, tool: 5, pathway: 3 },
};

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(payload),
      } as unknown as Response),
    ),
  );
});
afterEach(() => {
  vi.unstubAllGlobals();
});

// Import after stubbing is fine — module reads fetch at call time.
import Landing from '../src/pages/Landing';

describe('Landing', () => {
  it('renders the hero wordmark and the framework explanation', async () => {
    render(
      <MemoryRouter>
        <Landing />
      </MemoryRouter>,
    );
    expect(screen.getByRole('heading', { name: 'Synapse' })).toBeTruthy();
    expect(screen.getByText(/three layers/i)).toBeTruthy();
    await waitFor(() => expect(screen.getByTestId('count-skill').textContent).toBe('37'));
  });

  it('shows live counts per artifact class from the API', async () => {
    render(
      <MemoryRouter>
        <Landing />
      </MemoryRouter>,
    );
    await waitFor(() =>
      expect(screen.getByTestId('count-skill').textContent).toBe('37'),
    );
    expect(screen.getByTestId('count-agent').textContent).toBe('34');
    expect(screen.getByTestId('count-pathway').textContent).toBe('3');
  });

  it('links to the GitHub repo', async () => {
    render(
      <MemoryRouter>
        <Landing />
      </MemoryRouter>,
    );
    const link = screen.getByRole('link', { name: /GitHub repo/i });
    expect(link.getAttribute('href')).toBe('https://github.com/JuanSync7/ai-synapse');
    await waitFor(() => expect(screen.getByTestId('count-skill').textContent).toBe('37'));
  });
});
