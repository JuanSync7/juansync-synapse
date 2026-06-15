import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ExecResult, ScriptsResponse } from '../../shared/types';
import { getScripts, runScript } from '../src/api/client';
import Scripts from '../src/pages/Scripts';

vi.mock('../src/api/client', async () => {
  const actual = await vi.importActual<typeof import('../src/api/client')>('../src/api/client');
  return { ...actual, getScripts: vi.fn(), runScript: vi.fn() };
});

const mockGet = vi.mocked(getScripts);
const mockRun = vi.mocked(runScript);

const DATA: ScriptsResponse = {
  scripts: [
    {
      kind: 'script',
      name: 'validate',
      description: 'Run structural checks',
      audience: 'contributor',
      action: 'inspect',
      scope: 'repo',
      path: 'scripts/validate.sh',
      doc: '# cortex validate\n\nUse it before committing.',
    },
    {
      kind: 'script',
      name: 'reorganize',
      description: 'Reorganize artifacts',
      audience: 'maintainer',
      action: 'repair',
      scope: 'repo',
      path: 'scripts/reorganize.sh',
      doc: null,
    },
  ],
  cliCommands: [{ kind: 'cli-command', name: 'drift', doc: '# cortex drift\n\nResolve drift.' }],
};

beforeEach(() => mockGet.mockResolvedValue(DATA));
afterEach(() => vi.clearAllMocks());

describe('Scripts page', () => {
  it('renders a card per script + cli-command with audience badge', async () => {
    render(<Scripts />);
    await waitFor(() => expect(screen.getByText('validate')).toBeTruthy());
    expect(screen.getByText('reorganize')).toBeTruthy();
    expect(screen.getByText('drift')).toBeTruthy();
    expect(screen.getByText('contributor')).toBeTruthy();
    expect(screen.getByText('maintainer')).toBeTruthy();
  });

  it('marks a non-runnable script documentation-only', async () => {
    render(<Scripts />);
    await waitFor(() => expect(screen.getByText('reorganize')).toBeTruthy());
    // reorganize is not in the runnable allow-list.
    expect(screen.getAllByText('documentation-only').length).toBeGreaterThan(0);
  });

  it('runs an allow-listed command and shows the TerminalPane output', async () => {
    const result: ExecResult = {
      command: 'cortex validate',
      stdout: '0 errors / 0 warnings',
      stderr: '',
      exitCode: 0,
    };
    mockRun.mockResolvedValue(result);

    render(<Scripts />);
    await waitFor(() => expect(screen.getByText('validate')).toBeTruthy());

    fireEvent.click(screen.getByText(/Run cortex validate/i));

    await waitFor(() => expect(screen.getByTestId('terminal-pane')).toBeTruthy());
    expect(screen.getByText('0 errors / 0 warnings')).toBeTruthy();
    expect(screen.getByTestId('exit-badge').textContent).toContain('exit 0');
    expect(mockRun).toHaveBeenCalledWith('./cortex', ['validate']);
  });
});
