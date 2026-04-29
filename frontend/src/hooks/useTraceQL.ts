// src/hooks/useTraceQL.ts
import { useQuery } from '@tanstack/react-query';
import type { UseQueryResult } from '@tanstack/react-query';
import { queryTraceQL } from '../api/traceql';
import type { TraceQLRow } from '../api/traceql';
import type { TimeSeries } from '../types';
import { buildExperimentQuery } from '../queries/experiment';
import type { SelectQueryParams } from '../queries/experiment';

// Re-export SelectQueryParams so existing callers can still import from this hook
export type { SelectQueryParams };

// ── toTimeSeries ──────────────────────────────────────────────────────────────

/**
 * Convert row-format TraceQLRow[] to TimeSeries[] for chart rendering.
 * groupByField: the dimension field to create separate series for (e.g. 'scaffold').
 * When undefined, all rows are merged into a single series named after valueField.
 */
export function toTimeSeries(
  rows: TraceQLRow[],
  valueField: string,
  groupByField?: string
): TimeSeries[] {
  if (rows.length === 0) return [];

  const groups = new Map<string, TraceQLRow[]>();
  for (const row of rows) {
    const key = groupByField ? String(row[groupByField] ?? '') : '__all__';
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(row);
  }

  const series: TimeSeries[] = [];
  for (const [groupName, groupRows] of groups) {
    const sorted = [...groupRows].sort((a, b) => (a.iteration ?? 0) - (b.iteration ?? 0));
    series.push({
      name: groupName === '__all__' ? valueField : groupName,
      labels: groupByField ? { [groupByField]: groupName } : {},
      xAxisType: 'iteration',
      points: sorted.map(row => {
        let value = (row[valueField] as number) ?? 0;
        if (valueField === 'pass_rate') {
          value = Math.min(1, value);
        }
        return {
          iteration: row.iteration ?? 0,
          time: 0,
          value,
          labels: groupByField ? { [groupByField]: String(row[groupByField] ?? '') } : {},
        };
      }),
    });
  }
  return series;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export interface TraceQLHookOptions {
  enabled?: boolean;
  staleTime?: number;
  gcTime?: number;
  refetchOnMount?: boolean | 'always';
}

/**
 * Execute a TraceQL raw select query and return the row array.
 *
 * @param metricKey  Key in EXPERIMENT_METRIC_DEFS (e.g. 'reward_stats', 'pass_rate')
 * @param experimentId  Experiment ID to filter by
 * @param params  { filters: specific-value selector conditions, splitBy: group-by dimensions }
 * @param options  React Query options
 */
export function useTraceQL(
  metricKey: string,
  experimentId: string,
  params?: SelectQueryParams,
  options?: TraceQLHookOptions
): UseQueryResult<TraceQLRow[]> {
  const query = buildExperimentQuery(metricKey, experimentId, params);
  return useQuery({
    queryKey: ['traceql', query],
    queryFn: () => queryTraceQL(query),
    enabled: options?.enabled !== false,
    staleTime: options?.staleTime ?? 0,
    gcTime: options?.gcTime ?? 0,
    refetchOnMount: options?.refetchOnMount ?? 'always',
  });
}
