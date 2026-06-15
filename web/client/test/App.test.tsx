import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// Shell + Landing fetch counts on mount; stub the client so the shell test
// stays focused on routing/nav structure without a real network call.
vi.mock('../src/api/client', () => ({
  listArtifacts: vi.fn(() =>
    Promise.resolve({
      items: [],
      counts: { skill: 0, agent: 0, protocol: 0, tool: 0, pathway: 0 },
    }),
  ),
  getArtifact: vi.fn(),
  getPipeline: vi.fn(),
}));

import App from '../src/App';

const NAV_PATHS = [
  '/skills',
  '/agents',
  '/protocols',
  '/tools',
  '/pathways',
  '/registry',
  '/taxonomy',
  '/framework',
  '/memos',
  '/brainstorm',
  '/runs',
  '/scripts',
];

describe('app shell', () => {
  it('renders the left-rail nav with a link per surface', async () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    const links = screen.getAllByRole('link');
    const hrefs = links.map((l) => l.getAttribute('href'));
    expect(hrefs).toContain('/');
    for (const p of NAV_PATHS) {
      expect(hrefs).toContain(p);
    }
    // flush the mounted count-fetch state update so it lands inside act()
    await waitFor(() => expect(screen.getAllByText('0').length).toBeGreaterThan(0));
  });

  it('renders the Landing hero at /', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    );
    expect(await screen.findByRole('heading', { name: 'Synapse' })).toBeTruthy();
  });
});
