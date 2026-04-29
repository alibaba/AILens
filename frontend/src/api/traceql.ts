import apiClient from './client';

// ── 行式响应类型 ──

export type TraceQLRow = Record<string, never>;

export interface TraceQLOptions {
  pageSize?: number;
  pageNum?: number;
  start?: number;
  end?: number;
}

/**
 * 向后端代理 POST /trace/query，返回行式数据数组。
 */
export async function queryTraceQL(query: string, options?: TraceQLOptions): Promise<TraceQLRow[]> {
  const { data } = await apiClient.post('/trace/query', {
    query,
    page_size: options?.pageSize ?? 1000,
    page_num: options?.pageNum ?? 1,
    ...(options?.start !== undefined && { start: options.start }),
    ...(options?.end !== undefined && { end: options.end }),
  });
  const resp = data as { data?: TraceQLRow[] };
  return resp.data ?? [];
}
