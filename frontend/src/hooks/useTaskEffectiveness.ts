import { useMemo } from 'react';
import { useTraceQL } from './useTraceQL';
import type { SelectQueryParams } from './useTraceQL';
import type {
  TaskEffectivenessResponse,
  TaskEffectivenessItem,
  TaskClassification,
} from '../types';
import type { AnalysisFilterParams } from '../api/stats';

interface UseTaskEffectivenessOptions {
  enabled?: boolean;
}

function classify(validCount: number, passCount: number): TaskClassification {
  if (validCount === 0) return 'unverified';
  if (passCount === validCount) return 'all_pass';
  if (passCount === 0) return 'all_fail';
  return 'mixed';
}

/**
 * Hook for fetching task-level effectiveness data via a single TraceQL select query.
 * Groups by task_id + task_language; computes fail_count, classification, and summary in JS.
 *
 * When an iteration filter is specified it is applied as a selector condition (not a group-by
 * field), so results are aggregated per task across all trajectories in that iteration.
 */
export function useTaskEffectiveness(
  experimentId: string,
  filterParams?: AnalysisFilterParams,
  options?: UseTaskEffectivenessOptions,
  extraFilters?: Record<string, string | number | undefined>
) {
  const enabled = options?.enabled !== false;

  const queryParams = useMemo((): SelectQueryParams => {
    const filters: Record<string, string | number> = {};
    if (filterParams?.scaffold) filters.scaffold = filterParams.scaffold;
    if (filterParams?.language) filters.task_language = filterParams.language;
    if (filterParams?.tool_schema) filters.tool_schema = filterParams.tool_schema;
    if (filterParams?.iteration !== undefined) filters.iteration = filterParams.iteration;
    // Merge extra filters (e.g. dataset_name for dataset mode)
    if (extraFilters) {
      for (const [k, v] of Object.entries(extraFilters)) {
        if (v !== undefined) filters[k] = v;
      }
    }
    return {
      filters,
      omitIterationGroupBy: true,
    };
  }, [filterParams, extraFilters]);

  const hasScope = !!experimentId || !!extraFilters?.dataset_name;
  const { data: rows = [], isLoading } = useTraceQL(
    'task_effectiveness',
    experimentId,
    queryParams,
    { enabled: enabled && hasScope }
  );

  const data = useMemo<TaskEffectivenessResponse | undefined>(() => {
    if (rows.length === 0 && !isLoading) {
      return {
        summary: { all_pass: 0, all_fail: 0, mixed: 0, unverified: 0, total: 0 },
        tasks: [],
      };
    }
    if (rows.length === 0) return undefined;

    const tasks: TaskEffectivenessItem[] = rows
      .map(row => {
        const trajectoryCount = row.rollout_count ?? 0;
        const validCount = row.valid_count ?? 0;
        const passCount = row.pass_count ?? 0;
        const failCount = validCount - passCount;
        const classification = classify(validCount, passCount);
        const firstPassRaw = row.first_pass_iteration ?? 0;
        const firstPassIteration = passCount > 0 && firstPassRaw > 0 ? firstPassRaw : null;

        return {
          task_id: String(row.task_id ?? ''),
          language: String(row.task_language ?? 'unknown'),
          scaffold: String(row.scaffold ?? ''),
          tool_schema: String(row.tool_schema ?? ''),
          dataset_name: String(row.dataset_name ?? ''),
          rollout_count: trajectoryCount,
          valid_count: validCount,
          pass_count: passCount,
          fail_count: failCount,
          pass_rate: row.pass_rate ?? 0,
          first_pass_iteration: firstPassIteration,
          classification,
        };
      })
      .sort((a, b) => a.pass_rate - b.pass_rate);

    const summary = tasks.reduce(
      (acc, t) => {
        acc[t.classification] += 1;
        acc.total += 1;
        return acc;
      },
      { all_pass: 0, all_fail: 0, mixed: 0, unverified: 0, total: 0 }
    );

    return { summary, tasks };
  }, [rows, isLoading]);

  return { data, isLoading };
}
