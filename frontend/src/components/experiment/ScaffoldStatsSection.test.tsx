import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ScaffoldStatsSection from './ScaffoldStatsSection';

// Mock the useTraceQL hook
vi.mock('../../hooks/useTraceQL', () => ({
  useTraceQL: vi.fn(),
}));

import { useTraceQL } from '../../hooks/useTraceQL';
const mockUseTraceQLView = vi.mocked(useTraceQL);

const SCAFFOLD_ROWS = [
  {
    scaffold: 'Python CLI',
    trajectory_count: 40,
    pass_rate: 0.8,
    mean_reward: 0.75,
    mean_turns: 3.5,
    tokens_per_traj: 2500,
    total_duration_ms: 5000,
  },
  {
    scaffold: 'Web Automation',
    trajectory_count: 20,
    pass_rate: 0.6,
    mean_reward: 0.55,
    mean_turns: 4.2,
    tokens_per_traj: 3000,
    total_duration_ms: 6000,
  },
];

describe('ScaffoldStatsSection', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    document.body.innerHTML = '';
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    mockUseTraceQLView.mockReturnValue({
      data: SCAFFOLD_ROWS,
      isLoading: false,
    } as ReturnType<typeof useTraceQL>);
  });

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ScaffoldStatsSection experimentId="test-experiment" />
      </QueryClientProvider>
    );
  };

  it('renders Scaffold Stats table with correct header', () => {
    renderComponent();

    expect(screen.getByText(/Scaffold\s+Stats/)).toBeInTheDocument();
    expect(screen.getByText('Trajectories')).toBeInTheDocument();
    expect(screen.queryByText('频次')).not.toBeInTheDocument();
  });

  it('renders data rows correctly', () => {
    renderComponent();

    expect(screen.getByText('Python CLI')).toBeInTheDocument();
    expect(screen.getByText('Web Automation')).toBeInTheDocument();
    expect(screen.getByText('40')).toBeInTheDocument();
    expect(screen.getByText('20')).toBeInTheDocument();
  });

  it('renders summary row at the bottom', () => {
    renderComponent();

    const summaryRow = screen.getByText('Total');
    expect(summaryRow).toBeInTheDocument();

    // total count: 40 + 20 = 60
    expect(screen.getByText('60')).toBeInTheDocument();
  });

  it('uses single scaffold_stats metric query with omitIterationGroupBy', () => {
    renderComponent();

    expect(mockUseTraceQLView).toHaveBeenCalledWith(
      'scaffold_stats',
      'test-experiment',
      { splitBy: ['scaffold'], omitIterationGroupBy: true },
      { enabled: true }
    );
    // All calls must use scaffold_stats (React may render multiple times)
    const metricKeys = mockUseTraceQLView.mock.calls.map(call => call[0]);
    expect(metricKeys.every(k => k === 'scaffold_stats')).toBe(true);
  });

  it('summary row stays at bottom during sorting by count', () => {
    renderComponent();

    const trajectoryHeader = screen.getByText('Trajectories');
    fireEvent.click(trajectoryHeader);

    const rows = screen.getAllByRole('row');
    const lastDataRow = rows[rows.length - 1];
    expect(lastDataRow).toHaveTextContent('Total');
  });

  it('summary row stays at bottom during sorting by pass rate', () => {
    renderComponent();

    const passRateHeader = screen.getByText('Pass%');
    fireEvent.click(passRateHeader);

    const rows = screen.getAllByRole('row');
    const lastDataRow = rows[rows.length - 1];
    expect(lastDataRow).toHaveTextContent('Total');
  });

  it('summary row stays at bottom during sorting by avg reward', () => {
    renderComponent();

    const avgRewardHeader = screen.getByText('AvgReward');
    fireEvent.click(avgRewardHeader);

    const rows = screen.getAllByRole('row');
    const lastDataRow = rows[rows.length - 1];
    expect(lastDataRow).toHaveTextContent('Total');
  });

  it('summary row stays at bottom during sorting by avg turns', () => {
    renderComponent();

    const avgTurnsHeader = screen.getByText('AvgTurns');
    fireEvent.click(avgTurnsHeader);

    const rows = screen.getAllByRole('row');
    const lastDataRow = rows[rows.length - 1];
    expect(lastDataRow).toHaveTextContent('Total');
  });

  it('summary row stays at bottom during sorting by avg tokens', () => {
    renderComponent();

    const avgTokensHeader = screen.getByText('AvgTokens');
    fireEvent.click(avgTokensHeader);

    const rows = screen.getAllByRole('row');
    const lastDataRow = rows[rows.length - 1];
    expect(lastDataRow).toHaveTextContent('Total');
  });

  it('summary row stays at bottom during sorting by avg duration', () => {
    renderComponent();

    const avgDurationHeader = screen.getByText('AvgDuration');
    fireEvent.click(avgDurationHeader);

    const rows = screen.getAllByRole('row');
    const lastDataRow = rows[rows.length - 1];
    expect(lastDataRow).toHaveTextContent('Total');
  });

  it('displays all required columns', () => {
    renderComponent();

    expect(screen.getByText('Scaffold')).toBeInTheDocument();
    expect(screen.getByText('Trajectories')).toBeInTheDocument();
    expect(screen.getByText('Passed')).toBeInTheDocument();
    expect(screen.getByText('Pass%')).toBeInTheDocument();
    expect(screen.getByText('AvgReward')).toBeInTheDocument();
    expect(screen.getByText('AvgTurns')).toBeInTheDocument();
    expect(screen.getByText('AvgTokens')).toBeInTheDocument();
    expect(screen.getByText('AvgDuration')).toBeInTheDocument();
  });

  it('shows loading state when isLoading is true', () => {
    mockUseTraceQLView.mockReturnValue({
      data: [],
      isLoading: true,
    } as ReturnType<typeof useTraceQL>);

    renderComponent();

    expect(screen.getByText('Loading scaffold stats...')).toBeInTheDocument();
  });

  it('handles empty data gracefully', () => {
    mockUseTraceQLView.mockReturnValue({
      data: [],
      isLoading: false,
    } as ReturnType<typeof useTraceQL>);

    renderComponent();

    expect(screen.getByText('No scaffold data available')).toBeInTheDocument();
  });
});
