import { useQuery } from '@tanstack/react-query';
import apiClient from './client';

// ── Types (consistent with backend) ──

export type SpanStatus = 'ok' | 'error' | 'unset';

export interface SpanAttribute {
  key: string;
  value: string;
}

export interface SpanEvent {
  name: string;
  timestamp: number;
  attributes?: Record<string, string>;
}

export interface Span {
  span_id: string;
  trace_id: string;
  parent_span_id: string | null;
  operation_name: string;
  service_name: string;
  start_time: number;
  duration_ms: number;
  status: SpanStatus;
  status_message: string | null;
  attributes: SpanAttribute[];
  events: SpanEvent[];
  span_kind: string;
}

export interface Trace {
  trace_id: string;
  spans: Span[];
  duration_ms: number;
  span_count: number;
  has_error: boolean;
  root_operation: string | null;
  root_service: string | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  trace?: Record<string, any>; // Legacy field - dynamic API data
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  rl_context?: Record<string, any>; // Legacy field - dynamic API data
}

export interface SpanData {
  span_id: string;
  trace_id: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any; // Dynamic span data from tracing system
}

export interface RLContext {
  context_id?: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any; // Dynamic RL context data
}

export interface TraceSearchResult {
  trace_id: string;
  start_time: number;
  duration_ms: number;
  span_count: number;
  status: SpanStatus;
  root_operation: string | null;
  root_service: string | null;
}

// ── Hooks ──

export interface UseTraceOptions {
  provider?: string;
  enabled?: boolean;
}

export function useTrace(traceId: string | undefined, options: UseTraceOptions = {}) {
  const { provider, enabled = true } = options;

  return useQuery<Trace>({
    queryKey: ['trace', traceId, provider],
    queryFn: async () => {
      const params = provider ? { provider } : {};
      const { data } = await apiClient.get(`/traces/${traceId}`, { params });
      return data;
    },
    enabled: !!traceId && enabled,
    staleTime: Infinity,
  });
}

export interface TraceSearchParams {
  start_time: number;
  end_time: number;
  service_name?: string;
  operation_name?: string;
  status?: string;
  provider?: string;
  limit?: number;
}

export function useTraceSearch(params: TraceSearchParams) {
  return useQuery<TraceSearchResult[]>({
    queryKey: ['traces-search', params],
    queryFn: async () => {
      const { data } = await apiClient.get('/traces/search', { params });
      return data;
    },
    staleTime: 0,
  });
}

export function useTraceUrl(traceId: string | undefined, provider?: string) {
  return useQuery<{ trace_id: string; url: string }>({
    queryKey: ['trace-url', traceId, provider],
    queryFn: async () => {
      const params = provider ? { provider } : {};
      const { data } = await apiClient.get(`/traces/${traceId}/url`, { params });
      return data;
    },
    enabled: !!traceId,
    staleTime: Infinity,
  });
}
