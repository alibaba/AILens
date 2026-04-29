import { useMemo } from 'react';
import { useTraceQL, toTimeSeries } from './useTraceQL';
import type { SelectQueryParams } from './useTraceQL';
import type { TimeSeries } from '../types';
import type { AnalysisFilterParams } from '../api/stats';

interface TaskTrendItem {
  taskId: string;
  range: number; // max(pass_rate) - min(pass_rate) across iterations
}

export interface UseTaskPassRateTrendResult {
  /** One TimeSeries per task, each with points sorted by iteration */
  allSeries: TimeSeries[];
  /** Tasks ranked by pass rate change (descending), for default Top N selection */
  rankedTasks: TaskTrendItem[];
  isLoading: boolean;
}

export function useTaskPassRateTrend(
  experimentId: string,
  filterParams?: AnalysisFilterParams,
  options?: { enabled?: boolean }
): UseTaskPassRateTrendResult {
  const enabled = options?.enabled !== false;

  const queryParams = useMemo((): SelectQueryParams => {
    const filters: Record<string, string | number> = {};
    if (filterParams?.scaffold) filters.scaffold = filterParams.scaffold;
    if (filterParams?.language) filters.task_language = filterParams.language;
    // Note: do NOT pass iteration as a filter — we want all iterations for the trend
    return {
      filters,
      omitIterationGroupBy: false, // key: include iteration in group-by
    };
  }, [filterParams]);

  const { data: rows = [], isLoading } = useTraceQL(
    'task_effectiveness',
    experimentId,
    queryParams,
    { enabled }
  );

  const allSeries = useMemo(() => toTimeSeries(rows, 'pass_rate', 'task_id'), [rows]);

  const rankedTasks = useMemo<TaskTrendItem[]>(() => {
    return allSeries
      .map(s => {
        const values = s.points.map(p => p.value);
        if (values.length === 0) return { taskId: s.name, range: 0 };
        const min = Math.min(...values);
        const max = Math.max(...values);
        return { taskId: s.name, range: max - min };
      })
      .sort((a, b) => b.range - a.range);
  }, [allSeries]);

  return { allSeries, rankedTasks, isLoading };
}
