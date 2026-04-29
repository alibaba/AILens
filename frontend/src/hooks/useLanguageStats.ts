import { useMemo } from 'react';
import { useTraceQL } from './useTraceQL';
import type { SelectQueryParams } from './useTraceQL';
import type { LanguageStatsItem } from '../types';
import type { AnalysisFilterParams } from '../api/stats';

interface UseLanguageStatsOptions {
  enabled?: boolean;
}

/**
 * Hook for fetching Language Stats via a single TraceQL select query.
 * Groups by task_language; computes pass rate, turns and duration in one round-trip.
 *
 * When no iteration is specified (ALL), omits iteration from the by() clause so results
 * are aggregated across all iterations rather than broken down per iteration.
 */
export function useLanguageStats(
  experimentId: string,
  filterParams?: AnalysisFilterParams,
  options?: UseLanguageStatsOptions
) {
  const enabled = options?.enabled !== false;
  const hasIterationFilter = filterParams?.iteration !== undefined;

  const queryParams = useMemo((): SelectQueryParams => {
    const filters: Record<string, string | number> = {};
    if (filterParams?.scaffold) filters.scaffold = filterParams.scaffold;
    if (filterParams?.language) filters.task_language = filterParams.language;
    if (hasIterationFilter) filters.iteration = filterParams!.iteration!;
    return {
      filters,
      splitBy: ['task_language'],
      omitIterationGroupBy: !hasIterationFilter,
    };
  }, [filterParams, hasIterationFilter]);

  const { data: rows = [], isLoading } = useTraceQL('language_stats', experimentId, queryParams, {
    enabled,
  });

  const data = useMemo<LanguageStatsItem[]>(() => {
    if (rows.length === 0) return [];

    return rows.map(row => {
      const passedCount = row.passed_count ?? 0;
      return {
        language: String(row.task_language ?? 'unknown'),
        count: row.trajectory_count ?? 0,
        pass_rate: row.pass_rate ?? 0,
        max_turns_passed: row.max_turns_passed ?? 0,
        avg_turns_passed: passedCount > 0 ? (row.sum_turns_passed ?? 0) / passedCount : 0,
        max_duration_passed_ms: row.max_duration_passed_ms ?? 0,
        avg_duration_passed_ms:
          passedCount > 0 ? (row.sum_duration_passed_ms ?? 0) / passedCount : 0,
      };
    });
  }, [rows]);

  return { data, isLoading };
}
