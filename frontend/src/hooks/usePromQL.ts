import { useQuery } from '@tanstack/react-query';
import {
  queryRange,
  parsePromQLResult,
  buildAggregationQuery,
  type TimeSeries,
  type PromQLParams,
} from '../api/promql';

export type { TimeSeries };

interface UsePromQLOptions {
  enabled?: boolean;
  staleTime?: number;
}

interface AggregationOptions {
  aggFunc?: 'sum' | 'avg' | 'max' | 'min' | 'count' | 'none';
  groupBy?: string[];
}

/**
 * Generic PromQL range-query hook.
 * Returns parsed `TimeSeries[]` ready for charting.
 */
export function usePromQL(query: string, params?: PromQLParams, options?: UsePromQLOptions) {
  return useQuery({
    queryKey: ['promql', query, params],
    queryFn: async () => {
      const response = await queryRange(query, params);
      return parsePromQLResult(response);
    },
    enabled: options?.enabled !== false && !!query,
    staleTime: options?.staleTime ?? 60_000,
  });
}

/**
 * Convenience hook: single metric with experiment_id + optional extra labels.
 * Supports aggregation via `aggFunc` and `groupBy` options.
 */
export function usePromQLMetric(
  metricName: string,
  experimentId: string,
  extraLabels?: Record<string, string>,
  options?: UsePromQLOptions & AggregationOptions
) {
  const labels = { experiment_id: experimentId, ...extraLabels };
  const aggFunc = options?.aggFunc ?? 'none';
  const groupBy = options?.groupBy ?? [];

  const query = buildAggregationQuery(aggFunc, metricName, labels, groupBy);
  return usePromQL(query, undefined, options);
}
