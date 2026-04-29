import { useMemo, useState } from 'react';
import { Collapse } from 'antd';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts/core';
import { LineChart, BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import MetricCard from '../../components/shared/MetricCard';
import ChartPanel from '../../components/shared/ChartPanel';
import { useMetricsQuery, useMetricsRange, type MetricRangeSeries } from '../../api/metrics';
import { colors, fontSize } from '../../styles/theme';
import { mergeChartOption, CHART_COLORS } from '../../styles/echarts-dark';
import styles from './styles.module.css';
import type { EChartsOption } from 'echarts';

echarts.use([
  LineChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  CanvasRenderer,
]);

// ── Helpers ──

function fmt(v: number, unit: string): string {
  if (unit === 'ms') return v >= 1000 ? `${(v / 1000).toFixed(1)}s` : `${Math.round(v)}ms`;
  if (unit === 'pct') return `${(v * 100).toFixed(2)}%`;
  if (unit === 'k') return v >= 1000 ? `${(v / 1000).toFixed(1)}K` : `${Math.round(v)}`;
  return `${Math.round(v)}`;
}

/** Group range series by metric_name */
function groupByMetric(series: MetricRangeSeries[]) {
  const map: Record<string, MetricRangeSeries[]> = {};
  for (const s of series) {
    (map[s.metric_name] ??= []).push(s);
  }
  return map;
}

/** Average values across all series for a given metric */
function avgTimeSeries(seriesList: MetricRangeSeries[]): {
  timestamps: string[];
  values: number[];
} {
  if (!seriesList || seriesList.length === 0) return { timestamps: [], values: [] };
  // Use first series timestamps as base
  const base = seriesList[0].values;
  const timestamps = base.map(v => v.timestamp);
  const values = timestamps.map((_, i) => {
    let sum = 0;
    let count = 0;
    for (const s of seriesList) {
      if (s.values[i]) {
        sum += s.values[i].value;
        count++;
      }
    }
    return count > 0 ? sum / count : 0;
  });
  return { timestamps, values };
}

/** Build per-agent line series for a metric */
function perAgentLineSeries(seriesList: MetricRangeSeries[]): {
  timestamps: string[];
  lines: { name: string; data: number[] }[];
} {
  if (!seriesList || seriesList.length === 0) return { timestamps: [], lines: [] };
  const timestamps = seriesList[0].values.map(v => v.timestamp);
  const lines = seriesList.map((s, idx) => ({
    name: s.labels.agent || `series-${idx}`,
    data: s.values.map(v => v.value),
  }));
  return { timestamps, lines };
}

function timeLabels(timestamps: string[]): string[] {
  return timestamps.map(t => {
    const d = new Date(t);
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  });
}

function lineChartOption(
  timestamps: string[],
  lines: { name: string; data: number[] }[],
  yName = ''
): EChartsOption {
  return mergeChartOption({
    xAxis: { type: 'category', data: timeLabels(timestamps) },
    yAxis: {
      type: 'value',
      name: yName,
      nameTextStyle: { color: '#6B7280', fontSize: fontSize.axis },
    },
    legend: { bottom: 0, textStyle: { color: colors.textSecondary, fontSize: fontSize.sm } },
    series: lines.map((line, i) => ({
      name: line.name,
      type: 'line' as const,
      data: line.data,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2 },
      itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
    })),
    grid: { top: 32, right: 16, bottom: 40, left: 56 },
  });
}

function barChartOption(
  categories: string[],
  values: number[],
  barColor: string = colors.brand
): EChartsOption {
  return mergeChartOption({
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { rotate: 15, fontSize: fontSize.axis },
    },
    yAxis: { type: 'value' },
    series: [
      {
        type: 'bar',
        data: values,
        itemStyle: { color: barColor, borderRadius: [3, 3, 0, 0] },
        barMaxWidth: 36,
      },
    ],
    grid: { top: 24, right: 16, bottom: 48, left: 56 },
  });
}

// ── Section wrapper ──

function SectionRow({ children }: { children: React.ReactNode }) {
  return <div className={styles.sectionRow}>{children}</div>;
}

function HalfPanel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className={styles.halfPanel}>
      <ChartPanel title={title}>{children}</ChartPanel>
    </div>
  );
}

// ── Component ──

export default function ServiceMonitor() {
  const { data: instantData } = useMetricsQuery();
  const { data: rangeData } = useMetricsRange();

  // Compute KPI values from instant metrics
  const kpis = useMemo(() => {
    if (!instantData?.series) return { agents: 0, rpm: 0, p99: 0, errorRate: 0, tokenMin: 0 };
    const series = instantData.series;
    const agents = new Set(series.map(s => s.labels.agent));
    const rpmSeries = series.filter(s => s.metric_name === 'agent_request_rpm');
    const p99Series = series.filter(s => s.metric_name === 'agent_request_latency_p99_ms');
    const errSeries = series.filter(s => s.metric_name === 'agent_error_rate');
    const tokSeries = series.filter(s => s.metric_name === 'agent_llm_tokens_per_min');

    const sum = (arr: typeof rpmSeries) => arr.reduce((s, x) => s + x.value.value, 0);
    const avg = (arr: typeof rpmSeries) => (arr.length ? sum(arr) / arr.length : 0);

    return {
      agents: agents.size,
      rpm: Math.round(sum(rpmSeries)),
      p99: Math.round(avg(p99Series)),
      errorRate: avg(errSeries),
      tokenMin: Math.round(sum(tokSeries)),
    };
  }, [instantData]);

  // Group range data
  const grouped = useMemo(() => groupByMetric(rangeData?.series ?? []), [rangeData]);

  // ── LLM Layer charts ──
  const llmLatency = useMemo(() => {
    const s = grouped['agent_request_latency_p99_ms'] ?? [];
    const { timestamps, lines } = perAgentLineSeries(s);
    return lineChartOption(timestamps, lines, 'Latency (ms)');
  }, [grouped]);

  const llmErrorRate = useMemo(() => {
    const s = grouped['agent_error_rate'] ?? [];
    const { timestamps, lines } = perAgentLineSeries(s);
    // Convert to percentage
    const pctLines = lines.map(l => ({
      ...l,
      data: l.data.map(v => v * 100),
    }));
    return lineChartOption(timestamps, pctLines, 'Error Rate (%)');
  }, [grouped]);

  // ── Tool Layer charts — derive from available data ──
  const toolSuccessRate = useMemo(() => {
    // Use per-agent bar chart of average (1 - error_rate) as proxy for tool success
    const errSeries = grouped['agent_error_rate'] ?? [];
    const agents = errSeries.map(s => s.labels.agent);
    const vals = errSeries.map(s => {
      const avg = s.values.reduce((sum, v) => sum + v.value, 0) / (s.values.length || 1);
      return Math.round((1 - avg) * 100);
    });
    return barChartOption(agents, vals, colors.success);
  }, [grouped]);

  const toolLatency = useMemo(() => {
    // Reuse latency data per agent as "tool latency" proxy
    const s = grouped['agent_request_latency_p99_ms'] ?? [];
    const { timestamps, lines } = perAgentLineSeries(s);
    return lineChartOption(timestamps, lines, 'ms');
  }, [grouped]);

  // ── Skill Layer ──
  const skillUsage = useMemo(() => {
    // Derive from concurrent requests as a proxy for skill usage
    const s = grouped['agent_concurrent_requests'] ?? [];
    const agents = s.map(sr => sr.labels.agent);
    const vals = s.map(sr => {
      return Math.round(sr.values.reduce((sum, v) => sum + v.value, 0));
    });
    return barChartOption(agents, vals, colors.info);
  }, [grouped]);

  // ── Cross-Layer ──
  const e2eLatency = useMemo(() => {
    const s = grouped['agent_request_latency_p99_ms'] ?? [];
    const { timestamps, values } = avgTimeSeries(s);
    return lineChartOption(timestamps, [{ name: 'Avg P99', data: values }], 'ms');
  }, [grouped]);

  const rpmChart = useMemo(() => {
    const s = grouped['agent_request_rpm'] ?? [];
    const { timestamps, lines } = perAgentLineSeries(s);
    return lineChartOption(timestamps, lines, 'RPM');
  }, [grouped]);

  // Collapse items
  const [activeKeys, setActiveKeys] = useState<string[]>(['llm', 'tool', 'skill', 'cross']);

  const collapseItems = [
    {
      key: 'llm',
      label: <span className={styles.collapseLabel}>🧠 LLM Layer</span>,
      children: (
        <SectionRow>
          <HalfPanel title="LLM Call Latency (P99)">
            <div className={styles.chartSlot}>
              <ReactECharts option={llmLatency} style={{ height: '100%' }} notMerge lazyUpdate />
            </div>
          </HalfPanel>
          <HalfPanel title="LLM Error Rate">
            <div className={styles.chartSlot}>
              <ReactECharts option={llmErrorRate} style={{ height: '100%' }} notMerge lazyUpdate />
            </div>
          </HalfPanel>
        </SectionRow>
      ),
    },
    {
      key: 'tool',
      label: <span className={styles.collapseLabel}>🔧 Tool Layer</span>,
      children: (
        <SectionRow>
          <HalfPanel title="Tool Call Success Rate">
            <div className={styles.chartSlot}>
              <ReactECharts
                option={toolSuccessRate}
                style={{ height: '100%' }}
                notMerge
                lazyUpdate
              />
            </div>
          </HalfPanel>
          <HalfPanel title="Tool Latency">
            <div className={styles.chartSlot}>
              <ReactECharts option={toolLatency} style={{ height: '100%' }} notMerge lazyUpdate />
            </div>
          </HalfPanel>
        </SectionRow>
      ),
    },
    {
      key: 'skill',
      label: <span className={styles.collapseLabel}>🎯 Skill Layer</span>,
      children: (
        <div className={styles.skillChartWrap}>
          <ChartPanel title="Skill Usage">
            <div className={styles.chartSlot}>
              <ReactECharts option={skillUsage} style={{ height: '100%' }} notMerge lazyUpdate />
            </div>
          </ChartPanel>
        </div>
      ),
    },
    {
      key: 'cross',
      label: <span className={styles.collapseLabel}>🔗 Cross-Layer</span>,
      children: (
        <SectionRow>
          <HalfPanel title="End-to-End Latency (Avg P99)">
            <div className={styles.chartSlot}>
              <ReactECharts option={e2eLatency} style={{ height: '100%' }} notMerge lazyUpdate />
            </div>
          </HalfPanel>
          <HalfPanel title="Requests per Minute">
            <div className={styles.chartSlot}>
              <ReactECharts option={rpmChart} style={{ height: '100%' }} notMerge lazyUpdate />
            </div>
          </HalfPanel>
        </SectionRow>
      ),
    },
  ];

  return (
    <div className={styles.container}>
      {/* Page title */}
      <h1 className={styles.pageTitle}>Agent Service Monitor</h1>

      {/* KPI cards */}
      <div className={styles.kpiRow}>
        <MetricCard title="Agents" value={kpis.agents} />
        <MetricCard title="RPM (Total)" value={kpis.rpm} />
        <MetricCard title="P99 Latency" value={fmt(kpis.p99, 'ms')} />
        <MetricCard
          title="Error Rate"
          value={fmt(kpis.errorRate, 'pct')}
          subtitle={kpis.errorRate < 0.05 ? '✓ Normal' : '⚠ High'}
        />
        <MetricCard title="Token / min" value={fmt(kpis.tokenMin, 'k')} />
      </div>

      {/* Collapsible sections */}
      <Collapse
        activeKey={activeKeys}
        onChange={keys => setActiveKeys(keys as string[])}
        ghost
        items={collapseItems}
        className={styles.collapseTransparent}
      />
    </div>
  );
}
