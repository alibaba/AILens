/**
 * ECharts dark theme options — shared base config for all charts.
 * Consistent with unified color system.
 */
import { tokens, getEChartsThemeConfig } from './colors';
import type { EChartsOption } from 'echarts';

export const CHART_COLORS = tokens.chart;

/** Shared axis, grid, tooltip styling for all charts */
export function darkBaseOption(overrides?: Partial<EChartsOption>): EChartsOption {
  const baseConfig = getEChartsThemeConfig();

  return {
    ...baseConfig,
    ...overrides,
  } as EChartsOption;
}

/** Merge dark base with chart-specific options (deep-ish merge) */
export function mergeChartOption(specific: EChartsOption): EChartsOption {
  const base = darkBaseOption();
  return {
    ...base,
    ...specific,
    textStyle: { ...(base.textStyle as object), ...((specific.textStyle as object) ?? {}) },
    grid: { ...(base.grid as object), ...((specific.grid as object) ?? {}) },
    tooltip: { ...(base.tooltip as object), ...((specific.tooltip as object) ?? {}) },
    legend:
      specific.legend !== undefined
        ? { ...(base.legend as object), ...((specific.legend as object) ?? {}) }
        : base.legend,
  };
}
