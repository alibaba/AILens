import { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import MetricCard from '../shared/MetricCard';
import ChartPanel from '../shared/ChartPanel';
import { useTraceQL } from '../../hooks/useTraceQL';
import type { SelectQueryParams } from '../../hooks/useTraceQL';
import { colors } from '../../styles/theme';
import { CHART_COLORS } from '../../styles/echarts-dark';

interface SuccessTurnsSectionProps {
  experimentId: string;
  filterParams?: SelectQueryParams;
  isActive?: boolean;
}

export default function SuccessTurnsSection({
  experimentId,
  filterParams,
  isActive = true,
}: SuccessTurnsSectionProps) {
  const { data: turnsStatsRows = [] } = useTraceQL(
    'success_turns_stats',
    experimentId,
    filterParams, // 不使用omitIterationGroupBy
    { enabled: isActive }
  );

  const { data: turnsDistRows = [] } = useTraceQL(
    'turns_distribution',
    experimentId,
    { ...filterParams, omitIterationGroupBy: true }, // turns_distribution可以使用omitIterationGroupBy
    { enabled: isActive }
  );

  // Calculate statistics from all iterations (聚合所有迭代数据)
  const statsCards = useMemo(() => {
    if (turnsStatsRows.length === 0)
      return { totalSuccess: 0, minTurns: 0, maxTurns: 0, meanTurns: 0 };

    // 聚合所有迭代的数据，而不是过滤最新迭代
    return {
      totalSuccess: turnsStatsRows.reduce((s, r) => s + (r.passed_count ?? 0), 0),
      minTurns: Math.min(...turnsStatsRows.map(r => r.min_turns ?? 999)),
      maxTurns: Math.max(...turnsStatsRows.map(r => r.max_turns ?? 0)),
      meanTurns:
        turnsStatsRows.reduce((s, r) => s + (r.mean_turns ?? 0), 0) / (turnsStatsRows.length || 1),
    };
  }, [turnsStatsRows]);

  // Build bar chart data from turns distribution (所有迭代聚合数据)
  const chartData = useMemo(() => {
    if (turnsDistRows.length === 0)
      return { xData: [] as string[], counts: [] as number[], passedCounts: [] as number[] };
    const sortedRows = turnsDistRows.sort((a, b) => (a.turns ?? 0) - (b.turns ?? 0));
    return {
      xData: sortedRows.map(r => String(r.turns ?? '')),
      counts: sortedRows.map(r => r.total_count ?? 0),
      passedCounts: sortedRows.map(r => r.passed_count ?? 0),
    };
  }, [turnsDistRows]);

  // Calculate P90/P99 from success trajectory counts only
  const percentiles = useMemo(() => {
    const { xData, passedCounts } = chartData;
    if (xData.length === 0) return { p90: 'N/A', p99: 'N/A' };
    const total = passedCounts.reduce((s, c) => s + c, 0);
    if (total === 0) return { p90: 'N/A', p99: 'N/A' };
    let cumulative = 0;
    let p90: string | null = null;
    let p99: string | null = null;
    for (let i = 0; i < xData.length; i++) {
      cumulative += passedCounts[i];
      if (!p90 && cumulative / total >= 0.9) p90 = xData[i];
      if (!p99 && cumulative / total >= 0.99) p99 = xData[i];
    }
    return { p90: p90 ?? xData[xData.length - 1], p99: p99 ?? xData[xData.length - 1] };
  }, [chartData]);

  if (statsCards.totalSuccess === 0) {
    return null;
  }

  const barOption = {
    tooltip: {
      trigger: 'axis' as const,
      formatter: (params: unknown) => {
        const paramArray = Array.isArray(params) ? params : [params];
        const param = paramArray[0];
        if (param && typeof param === 'object' && 'axisValue' in param && 'value' in param) {
          return `${param.axisValue} Turns<br/>Success Trajectories: ${param.value}`;
        }
        return '';
      },
    },
    xAxis: {
      type: 'category' as const,
      data: chartData.xData,
      name: 'Turns',
      axisLabel: { color: colors.textSecondary },
    },
    yAxis: {
      type: 'value' as const,
      name: 'Success Count',
      axisLabel: { color: colors.textSecondary },
    },
    series: [
      {
        type: 'bar' as const,
        data: chartData.passedCounts,
        itemStyle: { color: CHART_COLORS[2] },
        barWidth: '60%',
      },
    ],
    grid: { left: 60, right: 20, top: 40, bottom: 40 },
  };

  return (
    <div data-testid="success-turns-section">
      <ChartPanel title="Success Trajectory Turns Distribution">
        <div className="mb-4 grid grid-cols-6 gap-3">
          <MetricCard title="Total Success" value={statsCards.totalSuccess} />
          <MetricCard title="Min Turns" value={statsCards.minTurns} />
          <MetricCard title="Max Turns" value={statsCards.maxTurns} />
          <MetricCard title="Mean Turns" value={statsCards.meanTurns.toFixed(2)} />
          <MetricCard title="P90 Turns" value={percentiles.p90} />
          <MetricCard title="P99 Turns" value={percentiles.p99} />
        </div>
        <ReactECharts option={barOption} className="w-full" style={{ height: 280 }} />
      </ChartPanel>
    </div>
  );
}
