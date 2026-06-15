import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { EvalData } from '../../shared/types';
import EvalPanel from '../src/components/EvalPanel';

const data: EvalData = {
  raw: '...',
  isPlaceholder: false,
  groups: {
    execution: [
      { id: 'EVAL-E01', text: 'runs without error', checked: true },
      { id: 'EVAL-E02', text: 'handles empty input', checked: false },
    ],
    output: [{ id: 'EVAL-O01', text: 'emits valid frontmatter', checked: true }],
    other: [],
  },
};

describe('EvalPanel', () => {
  it('renders execution and output criterion groups', () => {
    render(<EvalPanel data={data} />);
    expect(screen.getByText('Execution')).toBeTruthy();
    expect(screen.getByText('Output')).toBeTruthy();
    expect(screen.getByText('EVAL-E01')).toBeTruthy();
    expect(screen.getByText('runs without error')).toBeTruthy();
    expect(screen.getByText('EVAL-O01')).toBeTruthy();
  });

  it('shows the placeholder banner when the eval is a placeholder', () => {
    render(<EvalPanel data={{ ...data, isPlaceholder: true }} />);
    expect(screen.getByText(/placeholder EVAL/i)).toBeTruthy();
  });

  it('does not show the placeholder banner for a real eval', () => {
    render(<EvalPanel data={data} />);
    expect(screen.queryByText(/placeholder EVAL/i)).toBeNull();
  });

  it('handles the no-eval empty state', () => {
    render(<EvalPanel data={null} />);
    expect(screen.getByText(/No EVAL\.md found/i)).toBeTruthy();
  });
});
