import apiClient from './client';

// ── Types ──

export interface PromQLParams {
  start?: string;
  end?: string;
  step?: string;
}

export interface MetricSample {
  metric: Record<string, string>; // __name__, experiment_id, scaffold, tool...
  values: [number, string][]; // [x_value, value] - x_value is iteration_num or timestamp
}

export interface PromQLResponse {
  status: string;
  data: {
    resultType: string;
    result: MetricSample[];
  };
}

// TimeSeries types are now defined in types/traceql.ts; re-exported here for backward compatibility.
import type { TimeSeries, TimeSeriesPoint } from '../types';
export type { TimeSeries, TimeSeriesPoint };

// ── API ──

export async function queryRange(query: string, params?: PromQLParams): Promise<PromQLResponse> {
  const { data } = await apiClient.post('/query', { query, ...params });
  return data;
}

// ── Parsing helpers ──

export function buildAggregationQuery(
  aggFunc: 'sum' | 'avg' | 'max' | 'min' | 'count' | 'none',
  metricName: string,
  labels: Record<string, string>,
  groupBy: string[]
): string {
  const labelStr = Object.entries(labels)
    .map(([k, v]) => `${k}="${v}"`)
    .join(', ');

  if (aggFunc === 'none' || groupBy.length === 0) {
    // No aggregation: return simple metric query
    return `${metricName}{${labelStr}}`;
  }

  const groupByStr = groupBy.join(', ');
  return `${aggFunc}(${metricName}{${labelStr}}) by (${groupByStr})`;
}

export function formatSeriesName(metric: Record<string, string>): string {
  return metric.scaffold ?? metric.tool ?? metric.recovery_type ?? metric.__name__ ?? 'unknown';
}

export function parsePromQLResult(response: PromQLResponse): TimeSeries[] {
  return response.data.result.map(sample => {
    const xAxisType = (sample.metric.x_axis_type === 'iteration' ? 'iteration' : 'timestamp') as
      | 'iteration'
      | 'timestamp';

    return {
      name: formatSeriesName(sample.metric),
      labels: sample.metric,
      xAxisType,
      points: sample.values.map(([x_val, val]) => ({
        time: xAxisType === 'timestamp' ? x_val : 0,
        iteration: xAxisType === 'iteration' ? x_val : 0,
        value: parseFloat(val),
        labels: sample.metric,
      })),
    };
  });
}
