import apiClient from './client';
import type {
  ScaffoldStatsResponse,
  IterationsResponse,
  PassRateDiffResponse,
  CrossAnalysisResponse,
  RepetitionDetectionResponse,
  ExtremeCasesResponse,
  ToolQualityItem,
  ToolLatencyItem,
} from '../types';

// ── Filter params shared by all analysis endpoints ──

export interface AnalysisFilterParams {
  scaffold?: string;
  language?: string;
  tool_schema?: string;
  iteration?: number;
}

// ── Tool Analysis Aggregated API (REQ-004) ──

export interface ToolAnalysisItem {
  tool: string;
  scaffold: string;
  call_count: number;
  success_rate: number;
  avg_ms: number;
  p50_ms: number;
  p99_ms: number;
  trajectory_count: number;
  error_task_rate: number;
  success_task_rate: number;
}

export interface ToolAnalysisResponse {
  items: ToolAnalysisItem[];
}

/**
 * Fetch aggregated tool analysis metrics in a single API call.
 * This replaces multiple TraceQL queries (9 requests -> 1 request).
 *
 * @param experimentId - Required experiment ID
 * @param params - Optional filters (scaffold, language, tool_schema) and split_by
 */
export async function fetchToolAnalysis(
  experimentId: string,
  params?: AnalysisFilterParams & { split_by?: 'none' | 'scaffold' | 'language' | 'tool_schema' }
): Promise<ToolAnalysisResponse> {
  const response = await apiClient.post('/stats/tool-analysis', {
    experiment_id: experimentId,
    ...params,
  });
  return response.data;
}

/**
 * Convert ToolAnalysisResponse to ToolQualityItem[] for ToolQualitySection.
 * Maps the aggregated API response to the component's expected format.
 */
export function toToolQualityItems(items: ToolAnalysisItem[]): ToolQualityItem[] {
  return items.map(item => ({
    tool: item.tool,
    scaffold: item.scaffold,
    call_count: item.call_count,
    success_rate: item.success_rate,
    error_task_pct: item.error_task_rate,
    success_task_pct: item.success_task_rate,
    trajectory_count: item.trajectory_count,
    at_least_one_error_task_rate: item.error_task_rate,
    at_least_one_success_task_rate: item.success_task_rate,
  }));
}

/**
 * Convert ToolAnalysisResponse to ToolLatencyItem[] for ToolQualitySection.
 * Extracts latency metrics from the aggregated API response.
 */
export function toToolLatencyItems(items: ToolAnalysisItem[]): ToolLatencyItem[] {
  // Group by tool and aggregate latency metrics (for split_by != 'none')
  const latencyMap = new Map<
    string,
    { call_count: number; avg_ms: number; p50_ms: number; p99_ms: number }
  >();

  for (const item of items) {
    const existing = latencyMap.get(item.tool);
    if (existing) {
      // Weighted average for latency metrics
      const totalCalls = existing.call_count + item.call_count;
      existing.avg_ms =
        (existing.avg_ms * existing.call_count + item.avg_ms * item.call_count) / totalCalls;
      // For p50/p99, take the max of the values (simplified aggregation)
      existing.p50_ms = Math.max(existing.p50_ms, item.p50_ms);
      existing.p99_ms = Math.max(existing.p99_ms, item.p99_ms);
      existing.call_count = totalCalls;
    } else {
      latencyMap.set(item.tool, {
        call_count: item.call_count,
        avg_ms: item.avg_ms,
        p50_ms: item.p50_ms,
        p99_ms: item.p99_ms,
      });
    }
  }

  return Array.from(latencyMap.entries()).map(([tool, data]) => ({
    tool,
    call_count: data.call_count,
    avg_ms: data.avg_ms,
    p50_ms: data.p50_ms,
    p99_ms: data.p99_ms,
  }));
}

// ── Non-time-series analysis endpoints (path: /analysis/) ──

// fetchToolQuality and fetchToolLatency removed - endpoints deprecated
// Use fetchToolAnalysis for aggregated tool metrics (REQ-004)

export async function fetchScaffoldStats(
  experimentId: string,
  params?: AnalysisFilterParams
): Promise<ScaffoldStatsResponse> {
  const response = await apiClient.get(`/experiments/${experimentId}/analysis/scaffold`, {
    params,
  });
  return response.data;
}

export async function fetchLanguages(experimentId: string): Promise<{ languages: string[] }> {
  const response = await apiClient.get(`/experiments/${experimentId}/analysis/languages`);
  return response.data;
}

export async function fetchToolSchemas(experimentId: string): Promise<{ tool_schemas: string[] }> {
  const response = await apiClient.get(`/experiments/${experimentId}/analysis/tool-schemas`);
  return response.data;
}

// ── Non-analysis endpoints (unchanged) ──

export async function fetchIterations(experimentId: string): Promise<IterationsResponse> {
  const response = await apiClient.get(`/experiments/${experimentId}/iterations`);
  return response.data;
}

// ── M3: Pass Rate Diff ──

export async function fetchPassRateDiff(
  experimentId: string,
  stepA: number,
  stepB: number,
  params?: AnalysisFilterParams
): Promise<PassRateDiffResponse> {
  const response = await apiClient.get(`/experiments/${experimentId}/analysis/pass-rate-diff`, {
    params: { step_a: stepA, step_b: stepB, ...params },
  });
  return response.data;
}

export async function fetchCrossAnalysis(
  experimentId: string,
  stepA: number,
  stepB: number,
  rowDimension: string,
  colDimension: string
): Promise<CrossAnalysisResponse> {
  const response = await apiClient.get(`/experiments/${experimentId}/analysis/cross-analysis`, {
    params: {
      step_a: stepA,
      step_b: stepB,
      row_dimension: rowDimension,
      col_dimension: colDimension,
    },
  });
  return response.data;
}

// ── M4: Repetition Detection ──

export async function fetchRepetitionDetection(
  experimentId: string,
  params?: AnalysisFilterParams
): Promise<RepetitionDetectionResponse> {
  const response = await apiClient.get(
    `/experiments/${experimentId}/analysis/repetition-detection`,
    { params }
  );
  return response.data;
}

// ── M4: Extreme Cases ──

export async function fetchExtremeCases(
  experimentId: string,
  stepA: number,
  stepB: number,
  threshold?: number,
  type?: string
): Promise<ExtremeCasesResponse> {
  const response = await apiClient.get(`/experiments/${experimentId}/analysis/extreme-cases`, {
    params: { step_a: stepA, step_b: stepB, threshold: threshold ?? 0.2, type },
  });
  return response.data;
}
