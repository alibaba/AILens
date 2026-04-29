import { createElement } from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

vi.mock('../api/traceql', () => ({
  queryTraceQL: vi.fn(),
}));

import { queryTraceQL } from '../api/traceql';
import { toTimeSeries, useTraceQL } from './useTraceQL';

// ── toTimeSeries ──────────────────────────────────────────────────────────────

describe('toTimeSeries', () => {
  it('returns empty array for empty rows', () => {
    expect(toTimeSeries([], 'mean_reward')).toEqual([]);
  });

  it('single series when no groupByField', () => {
    const rows = [
      { iteration: 1, mean_reward: 0.5 },
      { iteration: 2, mean_reward: 0.6 },
    ];
    const result = toTimeSeries(rows, 'mean_reward');
    expect(result).toHaveLength(1);
    expect(result[0].xAxisType).toBe('iteration');
    expect(result[0].points[0]).toMatchObject({ iteration: 1, value: 0.5, time: 0 });
    expect(result[0].points[1]).toMatchObject({ iteration: 2, value: 0.6, time: 0 });
  });

  it('groups rows by scaffold dimension', () => {
    const rows = [
      { iteration: 1, mean_reward: 0.5, scaffold: 'a' },
      { iteration: 2, mean_reward: 0.6, scaffold: 'a' },
      { iteration: 1, mean_reward: 0.4, scaffold: 'b' },
      { iteration: 2, mean_reward: 0.55, scaffold: 'b' },
    ];
    const result = toTimeSeries(rows, 'mean_reward', 'scaffold');
    expect(result).toHaveLength(2);
    const aGroup = result.find(s => s.name === 'a')!;
    expect(aGroup.points[0]).toMatchObject({ iteration: 1, value: 0.5 });
    expect(aGroup.points[1]).toMatchObject({ iteration: 2, value: 0.6 });
  });

  it('sorts points by iteration ascending', () => {
    const rows = [
      { iteration: 3, mean_reward: 0.7 },
      { iteration: 1, mean_reward: 0.5 },
    ];
    const result = toTimeSeries(rows, 'mean_reward');
    expect(result[0].points[0].iteration).toBe(1);
    expect(result[0].points[1].iteration).toBe(3);
  });

  it('series name equals valueField when no groupBy', () => {
    const result = toTimeSeries([{ iteration: 1, mean_reward: 0.5 }], 'mean_reward');
    expect(result[0].name).toBe('mean_reward');
  });

  it('sets labels on points when groupByField is provided', () => {
    const rows = [{ iteration: 1, pass_rate: 0.8, scaffold: 'my_scaffold' }];
    const result = toTimeSeries(rows, 'pass_rate', 'scaffold');
    expect(result[0].points[0].labels).toEqual({ scaffold: 'my_scaffold' });
  });

  it('accepts any string as groupByField (not restricted to known dimensions)', () => {
    const rows = [
      { iteration: 1, mean_reward: 0.5, tool_schema: 'schema_a' },
      { iteration: 1, mean_reward: 0.7, tool_schema: 'schema_b' },
    ];
    const result = toTimeSeries(rows, 'mean_reward', 'tool_schema');
    expect(result).toHaveLength(2);
    expect(result.map(s => s.name).sort()).toEqual(['schema_a', 'schema_b']);
  });
});

// ── useTraceQL ───────────────────────────────────────────────────────────────

describe('useTraceQL', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.mocked(queryTraceQL).mockReset();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children);

  it('calls queryTraceQL with correct raw select query', async () => {
    const mockRows = [{ iteration: 1, mean_reward: 0.5 }];
    vi.mocked(queryTraceQL).mockResolvedValue(mockRows);

    const { result } = renderHook(() => useTraceQL('reward_stats', 'exp-001'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockRows);
    expect(queryTraceQL).toHaveBeenCalledWith(
      '{experiment_id="exp-001"}\n' +
        '| select(iteration, round(avg(reward), 4) as mean_reward, stddev(reward) as reward_std, count() as trajectory_count)\n' +
        '  by (iteration)'
    );
  });

  it('includes splitBy in the query by clause', async () => {
    vi.mocked(queryTraceQL).mockResolvedValue([]);

    renderHook(() => useTraceQL('reward_stats', 'exp-001', { splitBy: ['scaffold'] }), {
      wrapper,
    });

    await waitFor(() => expect(queryTraceQL).toHaveBeenCalled());
    const calledQuery = vi.mocked(queryTraceQL).mock.calls[0][0];
    expect(calledQuery).toContain('by (iteration, scaffold)');
    expect(calledQuery).toContain('scaffold,');
  });

  it('includes filters in the selector', async () => {
    vi.mocked(queryTraceQL).mockResolvedValue([]);

    renderHook(
      () =>
        useTraceQL('reward_stats', 'exp-001', {
          filters: { scaffold: 'x', iteration: 3 },
        }),
      { wrapper }
    );

    await waitFor(() => expect(queryTraceQL).toHaveBeenCalled());
    const calledQuery = vi.mocked(queryTraceQL).mock.calls[0][0];
    expect(calledQuery).toContain('scaffold="x"');
    expect(calledQuery).toContain('iteration="3"');
  });

  it('does not fetch when enabled=false', () => {
    renderHook(() => useTraceQL('reward_stats', 'exp-001', undefined, { enabled: false }), {
      wrapper,
    });
    expect(queryTraceQL).not.toHaveBeenCalled();
  });
});
