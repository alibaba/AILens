import { memo } from 'react';
import _ from 'lodash';
import ReactECharts from 'echarts-for-react';
import { mergeChartOption, CHART_COLORS } from '../../styles/echarts-dark';
import { getEChartsThemeConfig } from '../../styles/colors';
import styles from './TimeSeriesChart.module.css';

/** Theme yAxis is overwritten wholesale by chart option; merge it in so tick label color/splitLine stay correct */
const THEME_Y_AXIS = getEChartsThemeConfig().yAxis as Record<string, unknown>;
const THEME_AXIS_LABEL = (THEME_Y_AXIS.axisLabel as Record<string, unknown>) ?? {};

export interface TimeSeriesLine {
  name: string;
  data: (number | null)[];
  color?: string;
  /** Show ±1σ band — provide stddev values per point */
  stdData?: number[];
  /** Area opacity for the line itself (0-1) */
  areaOpacity?: number;
  yAxisIndex?: number;
  /** Render as dashed line */
  dashed?: boolean;
}

export interface TimeSeriesChartProps {
  xData: (string | number)[];
  lines: TimeSeriesLine[];
  height?: number;
  yAxisName?: string;
  yAxisMax?: number;
  yAxisFormatter?: (v: number) => string;
  /** Second Y axis config */
  y2AxisName?: string;
  y2AxisFormatter?: (v: number) => string;
  showLegend?: boolean;
  /** Show ±1σ tip at bottom */
  showSigmaTip?: boolean;
}

/** Return true when props are equal → skip re-render (avoids duplicate ECharts update animation). */
function timeSeriesChartPropsEqual(
  prev: TimeSeriesChartProps,
  next: TimeSeriesChartProps
): boolean {
  return (
    _.isEqual(prev.xData, next.xData) &&
    _.isEqual(prev.lines, next.lines) &&
    (prev.height ?? 280) === (next.height ?? 280) &&
    prev.yAxisName === next.yAxisName &&
    prev.yAxisMax === next.yAxisMax &&
    prev.yAxisFormatter === next.yAxisFormatter &&
    prev.y2AxisName === next.y2AxisName &&
    prev.y2AxisFormatter === next.y2AxisFormatter &&
    (prev.showLegend ?? false) === (next.showLegend ?? false) &&
    (prev.showSigmaTip ?? false) === (next.showSigmaTip ?? false)
  );
}

function TimeSeriesChart({
  xData,
  lines,
  height = 280,
  yAxisName,
  yAxisMax,
  yAxisFormatter,
  y2AxisName,
  y2AxisFormatter,
  showLegend = false,
  showSigmaTip = false,
}: TimeSeriesChartProps) {
  const series: object[] = [];
  let hasSigma = false;

  lines.forEach((line, idx) => {
    const lineColor = line.color ?? CHART_COLORS[idx % CHART_COLORS.length];

    // Main line
    series.push({
      name: line.name,
      type: 'line',
      data: line.data,
      smooth: true,
      lineStyle: {
        width: 2,
        color: lineColor,
        type: line.dashed ? ('dashed' as const) : ('solid' as const),
      },
      itemStyle: { color: lineColor },
      symbol: 'none',
      yAxisIndex: line.yAxisIndex ?? 0,
      areaStyle: line.areaOpacity
        ? {
            color: `${lineColor}${Math.round(line.areaOpacity * 255)
              .toString(16)
              .padStart(2, '0')}`,
          }
        : undefined,
    });

    // ±1σ bands
    if (line.stdData && line.stdData.length > 0) {
      hasSigma = true;
      const upper = line.data.map((v, i) => (v === null ? null : v + (line.stdData?.[i] ?? 0)));
      const lower = line.data.map((v, i) => (v === null ? null : v - (line.stdData?.[i] ?? 0)));

      series.push({
        name: `${line.name} +1σ`,
        type: 'line',
        data: upper,
        lineStyle: { width: 0 },
        symbol: 'none',
        stack: `sigma-${idx}`,
        areaStyle: { color: 'transparent' },
        yAxisIndex: line.yAxisIndex ?? 0,
      });
      series.push({
        name: `${line.name} -1σ`,
        type: 'line',
        data: lower,
        lineStyle: { width: 0 },
        symbol: 'none',
        yAxisIndex: line.yAxisIndex ?? 0,
      });
      // Fill between upper and lower using markArea-like approach
      // Actually use a band visualization: upper line + lower with area between
      // ECharts approach: use two lines with stack for band
      // Simpler: use a custom area style on the upper series
      series.pop(); // Remove the last push
      series.pop(); // Remove the upper push

      // Better approach: use areaStyle on the main line for the band
      series.push({
        name: `${line.name} ±1σ`,
        type: 'line',
        data: upper.map((u, i) => [xData[i], lower[i], u]),
        lineStyle: { width: 0 },
        symbol: 'none',
        yAxisIndex: line.yAxisIndex ?? 0,
        // Use custom rendering — just show the fill
        encode: { x: 0, y: [1, 2] },
      });
      // Actually, let's use the proven approach: upper and lower lines
      series.pop();

      series.push({
        name: `${line.name} upper`,
        type: 'line',
        data: upper,
        lineStyle: { opacity: 0 },
        symbol: 'none',
        stack: `confidence-${idx}`,
        stackStrategy: 'all',
        areaStyle: { opacity: 0 },
        yAxisIndex: line.yAxisIndex ?? 0,
        silent: true,
      });
      series.push({
        name: `${line.name} lower`,
        type: 'line',
        data: lower.map((l, i) => (l === null || upper[i] === null ? null : upper[i]! - l)),
        lineStyle: { opacity: 0 },
        symbol: 'none',
        stack: `confidence-${idx}`,
        stackStrategy: 'all',
        areaStyle: { color: lineColor, opacity: 0.12 },
        yAxisIndex: line.yAxisIndex ?? 0,
        silent: true,
      });
    }
  });

  const yAxes: object[] = [
    {
      ...THEME_Y_AXIS,
      type: 'value' as const,
      name: yAxisName,
      max: yAxisMax,
      axisLabel: {
        ...THEME_AXIS_LABEL,
        ...(yAxisFormatter ? { formatter: yAxisFormatter } : {}),
      },
    },
  ];

  if (y2AxisName || lines.some(l => l.yAxisIndex === 1)) {
    yAxes.push({
      ...THEME_Y_AXIS,
      type: 'value' as const,
      name: y2AxisName,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: {
        ...THEME_AXIS_LABEL,
        ...(y2AxisFormatter ? { formatter: y2AxisFormatter } : {}),
      },
    });
  }

  const legendNames = lines.map(l => l.name);

  // Custom tooltip formatter for consistent number formatting
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const tooltipFormatter = (params: any) => {
    if (!Array.isArray(params)) {
      params = [params];
    }

    let result = `${params[0].axisValue}<br/>`;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    params.forEach((param: any) => {
      // Skip confidence band data (±1σ, upper, lower series)
      if (
        param.seriesName.includes('±1σ') ||
        param.seriesName.includes('upper') ||
        param.seriesName.includes('lower')
      ) {
        return;
      }

      let value: number | string = param.value;
      if (typeof value === 'number') {
        // Use yAxisFormatter if available for the corresponding axis
        const axisIndex =
          param.seriesIndex !== undefined
            ? (((series[param.seriesIndex] as Record<string, unknown>)?.yAxisIndex as number) ?? 0)
            : 0;

        if (axisIndex === 1 && y2AxisFormatter) {
          value = y2AxisFormatter(value);
        } else if (axisIndex === 0 && yAxisFormatter) {
          value = yAxisFormatter(value);
        } else if (yAxisName && yAxisName.toLowerCase().includes('rate')) {
          // Format as percentage for rate metrics
          value = `${(value * 100).toFixed(2)}%`;
        } else {
          // Format as 2 decimal places for numeric values
          value = value.toFixed(2);
        }
      }

      result += `<span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${param.color}"></span>`;
      result += `${param.seriesName}: ${value}<br/>`;
    });
    return result;
  };

  const option = mergeChartOption({
    xAxis: { type: 'category' as const, data: xData },
    yAxis: yAxes.length === 1 ? yAxes[0] : yAxes,
    series,
    legend: showLegend ? { show: true, data: legendNames } : { show: false },
    grid: {
      top: 40,
      bottom: showLegend ? 40 : 24,
      left: 56,
      right: yAxes.length > 1 ? 56 : 16,
      containLabel: true,
    },
    tooltip: {
      trigger: 'axis',
      formatter: tooltipFormatter,
    },
  });

  return (
    <div>
      <ReactECharts option={option} style={{ height }} notMerge />
      {showSigmaTip && hasSigma && (
        <div className={styles.sigmaTip}>
          💡 The semi-transparent shaded band represents the ±1σ (standard deviation) interval,
          encompassing approximately 68% of the data distribution.
        </div>
      )}
    </div>
  );
}

export default memo(TimeSeriesChart, timeSeriesChartPropsEqual);
