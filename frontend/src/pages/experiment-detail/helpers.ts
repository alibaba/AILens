// Shared helper functions for experiment detail page

import type { TimeSeries } from '../../types';
import type { ChartLine } from './types';
import type { AnalysisFilterParams } from '../../api/stats';
import { CHART_COLORS } from '../../styles/echarts-dark';

/**
 * Convert TimeSeries[] into { xData, lines } for TimeSeriesChart.
 * Handles both iteration-based and timestamp-based series.
 */
export function toChartData(
  seriesList: TimeSeries[],
  opts?: {
    yAxisIndex?: number;
    areaOpacity?: number;
  }
): { xData: string[]; lines: ChartLine[] } {
  if (seriesList.length === 0) return { xData: [], lines: [] };

  // Use the first series' x-axis type
  const xAxisType = seriesList[0].xAxisType ?? 'timestamp';

  // Collect all unique x-keys across all series to handle sparse data when split by is active.
  // Without this, series with fewer points get misaligned on the category x-axis.
  const allXKeys = new Set<number>();
  for (const s of seriesList) {
    for (const p of s.points) {
      allXKeys.add(xAxisType === 'iteration' ? (p.iteration ?? 0) : p.time);
    }
  }
  const sortedXKeys = [...allXKeys].sort((a, b) => a - b);

  // Generate xData labels from the unified sorted x-keys
  const xData = sortedXKeys.map(x => {
    if (xAxisType === 'iteration') {
      return `#${x}`;
    } else {
      const date = new Date(x * 1000); // epoch seconds to milliseconds
      const hours = date.getHours().toString().padStart(2, '0');
      const minutes = date.getMinutes().toString().padStart(2, '0');
      return `${hours}:${minutes}`;
    }
  });

  const lines: ChartLine[] = seriesList.map((s, idx) => {
    // Build a lookup map so we can align each series to the unified x-axis.
    // Missing positions are filled with null so ECharts renders a gap instead of shifting values.
    const valueMap = new Map<number, number>();
    for (const p of s.points) {
      const xKey = xAxisType === 'iteration' ? (p.iteration ?? 0) : p.time;
      valueMap.set(xKey, p.value);
    }
    return {
      name: s.name,
      data: sortedXKeys.map(x => valueMap.get(x) ?? null),
      color: CHART_COLORS[idx % CHART_COLORS.length],
      yAxisIndex: opts?.yAxisIndex,
      areaOpacity: opts?.areaOpacity,
    };
  });

  return { xData, lines };
}

/**
 * Build extra PromQL labels from scaffold/language/tool_schema filters.
 */
export function buildFilterLabels(
  scaffoldFilter: string | undefined,
  languageFilter: string | undefined,
  extraLabels?: Record<string, string>,
  toolSchemaFilter?: string | undefined
): Record<string, string> | undefined {
  const labels: Record<string, string> = { ...extraLabels };
  if (scaffoldFilter) labels.scaffold = scaffoldFilter;
  if (languageFilter) labels.language = languageFilter;
  if (toolSchemaFilter) labels.tool_schema = toolSchemaFilter;
  return Object.keys(labels).length > 0 ? labels : undefined;
}

/**
 * Build a query string (including leading "?") for experiment filter state.
 * Returns an empty string when no filters are active.
 */
export function buildFilterQueryString(
  scaffoldFilter: string | undefined,
  languageFilter: string | undefined,
  toolSchemaFilter: string | undefined,
  iterationFilter: string
): string {
  const params = new URLSearchParams();
  if (scaffoldFilter) params.set('scaffold', scaffoldFilter);
  if (languageFilter) params.set('language', languageFilter);
  if (toolSchemaFilter) params.set('tool_schema', toolSchemaFilter);
  if (iterationFilter !== 'all') params.set('iteration', iterationFilter);
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

/**
 * Build AnalysisFilterParams from scaffold/language/tool_schema/iteration filters.
 */
export function buildFilterParams(
  scaffoldFilter: string | undefined,
  languageFilter: string | undefined,
  toolSchemaFilter?: string | undefined,
  iteration?: number | undefined
): AnalysisFilterParams | undefined {
  const params: AnalysisFilterParams = {};
  if (scaffoldFilter) params.scaffold = scaffoldFilter;
  if (languageFilter) params.language = languageFilter;
  if (toolSchemaFilter) params.tool_schema = toolSchemaFilter;
  if (iteration !== undefined) params.iteration = iteration;
  return Object.keys(params).length > 0 ? params : undefined;
}
