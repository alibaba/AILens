import { useQuery } from '@tanstack/react-query';
import apiClient from './client';

// ── Types ──

export interface MetricValue {
  timestamp: string;
  value: number;
}

export interface MetricSeries {
  metric_name: string;
  labels: Record<string, string>;
  value: MetricValue; // instant query
}

export interface MetricRangeSeries {
  metric_name: string;
  labels: Record<string, string>;
  values: MetricValue[]; // range query
}

export interface MetricsQueryResponse {
  series: MetricSeries[];
}

export interface MetricsRangeResponse {
  series: MetricRangeSeries[];
}

// ── Hooks ──

export function useMetricsQuery() {
  return useQuery<MetricsQueryResponse>({
    queryKey: ['metrics-query'],
    queryFn: () => apiClient.get('/metrics/query').then(r => r.data),
    staleTime: 15_000,
    refetchInterval: 15_000,
  });
}

export function useMetricsRange() {
  return useQuery<MetricsRangeResponse>({
    queryKey: ['metrics-range'],
    queryFn: () => apiClient.get('/metrics/range').then(r => r.data),
    staleTime: 15_000,
    refetchInterval: 15_000,
  });
}
