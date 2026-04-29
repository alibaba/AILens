import { useMemo } from 'react';
import { useTraceQL, toTimeSeries } from './useTraceQL';
import type { SelectQueryParams } from './useTraceQL';
import type { TimeSeries } from '../types';
import type { AnalysisFilterParams } from '../api/stats';

interface TaskTrendItem {
  taskId: string;
  range: number;
}

export interface UseTaskTurnsTrendResult {
  allSeries: TimeSeries[];
  rankedTasks: TaskTrendItem[];
  isLoading: boolean;
}

export function useTaskTurnsTrend(
  experimentId: string,
  filterParams?: AnalysisFilterParams,
  options?: { enabled?: boolean }
): UseTaskTurnsTrendResult {
  const enabled = options?.enabled !== false;

  const queryParams = useMemo((): SelectQueryParams => {
    const filters: Record<string, string | number> = {};
    if (filterParams?.scaffold) filters.scaffold = filterParams.scaffold;
    if (filterParams?.language) filters.task_language = filterParams.language;
    return {
      filters,
      omitIterationGroupBy: false,
    };
  }, [filterParams]);

  const { data: rows = [], isLoading } = useTraceQL('task_turns', experimentId, queryParams, {
    enabled,
  });

  const allSeries = useMemo(() => toTimeSeries(rows, 'mean_turns', 'task_id'), [rows]);

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
