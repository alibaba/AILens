import { createElement } from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

vi.mock('../api/traceql', () => ({
  queryTraceQL: vi.fn(),
}));

import { queryTraceQL } from '../api/traceql';
import { useTaskEffectiveness } from './useTaskEffectiveness';

describe('useTaskEffectiveness', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.mocked(queryTraceQL).mockReset();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children);

  it('returns undefined data while loading', () => {
    vi.mocked(queryTraceQL).mockResolvedValue([]);
    const { result } = renderHook(() => useTaskEffectiveness('exp-001'), { wrapper });
    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(true);
  });

  it('computes classification: all_pass when pass_count === valid_count', async () => {
    vi.mocked(queryTraceQL).mockResolvedValue([
      {
        task_id: 'task-1',
        task_language: 'python',
        rollout_count: 3,
        valid_count: 3,
        pass_count: 3,
        pass_rate: 1.0,
        first_pass_iteration: 2,
      },
    ]);

    const { result } = renderHook(() => useTaskEffectiveness('exp-001'), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    const task = result.current.data!.tasks[0];
    expect(task.classification).toBe('all_pass');
    expect(task.fail_count).toBe(0);
    expect(task.first_pass_iteration).toBe(2);
  });

  it('computes classification: all_fail when pass_count === 0 and valid_count > 0', async () => {
    vi.mocked(queryTraceQL).mockResolvedValue([
      {
        task_id: 'task-2',
        task_language: 'java',
        rollout_count: 2,
        valid_count: 2,
        pass_count: 0,
        pass_rate: 0,
        first_pass_iteration: 0,
      },
    ]);

    const { result } = renderHook(() => useTaskEffectiveness('exp-001'), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    const task = result.current.data!.tasks[0];
    expect(task.classification).toBe('all_fail');
    expect(task.fail_count).toBe(2);
    expect(task.first_pass_iteration).toBeNull();
  });

  it('computes classification: unverified when valid_count === 0', async () => {
    vi.mocked(queryTraceQL).mockResolvedValue([
      {
        task_id: 'task-3',
        task_language: 'go',
        rollout_count: 1,
        valid_count: 0,
        pass_count: 0,
        pass_rate: 0,
        first_pass_iteration: 0,
      },
    ]);

    const { result } = renderHook(() => useTaskEffectiveness('exp-001'), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.data!.tasks[0].classification).toBe('unverified');
  });

  it('computes classification: mixed when 0 < pass_count < valid_count', async () => {
    vi.mocked(queryTraceQL).mockResolvedValue([
      {
        task_id: 'task-4',
        task_language: 'ts',
        rollout_count: 4,
        valid_count: 4,
        pass_count: 2,
        pass_rate: 0.5,
        first_pass_iteration: 1,
      },
    ]);

    const { result } = renderHook(() => useTaskEffectiveness('exp-001'), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.data!.tasks[0].classification).toBe('mixed');
  });

  it('computes summary counts from tasks', async () => {
    vi.mocked(queryTraceQL).mockResolvedValue([
      {
        task_id: 't1',
        task_language: 'py',
        rollout_count: 2,
        valid_count: 2,
        pass_count: 2,
        pass_rate: 1,
        first_pass_iteration: 1,
      },
      {
        task_id: 't2',
        task_language: 'py',
        rollout_count: 2,
        valid_count: 2,
        pass_count: 0,
        pass_rate: 0,
        first_pass_iteration: 0,
      },
      {
        task_id: 't3',
        task_language: 'py',
        rollout_count: 1,
        valid_count: 0,
        pass_count: 0,
        pass_rate: 0,
        first_pass_iteration: 0,
      },
    ]);

    const { result } = renderHook(() => useTaskEffectiveness('exp-001'), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    const summary = result.current.data!.summary;
    expect(summary.all_pass).toBe(1);
    expect(summary.all_fail).toBe(1);
    expect(summary.unverified).toBe(1);
    expect(summary.mixed).toBe(0);
    expect(summary.total).toBe(3);
  });

  it('sorts tasks by pass_rate ascending', async () => {
    vi.mocked(queryTraceQL).mockResolvedValue([
      {
        task_id: 'high',
        task_language: 'py',
        rollout_count: 2,
        valid_count: 2,
        pass_count: 2,
        pass_rate: 1.0,
        first_pass_iteration: 1,
      },
      {
        task_id: 'low',
        task_language: 'py',
        rollout_count: 2,
        valid_count: 2,
        pass_count: 0,
        pass_rate: 0.0,
        first_pass_iteration: 0,
      },
    ]);

    const { result } = renderHook(() => useTaskEffectiveness('exp-001'), { wrapper });
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.data!.tasks[0].task_id).toBe('low');
    expect(result.current.data!.tasks[1].task_id).toBe('high');
  });

  it('uses iteration as selector filter when provided, not group-by', async () => {
    vi.mocked(queryTraceQL).mockResolvedValue([]);

    renderHook(() => useTaskEffectiveness('exp-001', { iteration: 5 }), { wrapper });

    await waitFor(() => expect(queryTraceQL).toHaveBeenCalled());
    const query = vi.mocked(queryTraceQL).mock.calls[0][0];
    expect(query).toContain('iteration="5"');
    expect(query).toContain('by (task_id, task_language, dataset_name)');
    expect(query).not.toContain('by (iteration');
  });

  it('does not fetch when disabled', () => {
    renderHook(() => useTaskEffectiveness('exp-001', undefined, { enabled: false }), { wrapper });
    expect(queryTraceQL).not.toHaveBeenCalled();
  });
});
