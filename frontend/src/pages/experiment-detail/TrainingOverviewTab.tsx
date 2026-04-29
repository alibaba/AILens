// Training Overview Tab - TraceQL view-based metrics display

import { useCallback, useMemo } from 'react';
import { Spin } from 'antd';
import ChartPanel from '../../components/shared/ChartPanel';
import MetricCard from '../../components/shared/MetricCard';
import TimeSeriesChart from '../../components/charts/TimeSeriesChart';
import ScaffoldStatsSection from '../../components/experiment/ScaffoldStatsSection';
import TurnAnalysisSection from '../../components/experiment/TurnAnalysisSection';
import SuccessTurnsSection from '../../components/experiment/SuccessTurnsSection';
import { usePromQLMetric } from '../../hooks/usePromQL';
import { useTraceQL, toTimeSeries } from '../../hooks/useTraceQL';
import type { SelectQueryParams } from '../../hooks/useTraceQL';
import { toChartData } from './helpers';
import { CHART_COLORS } from '../../styles/echarts-dark';
import styles from './styles.module.css';

interface TrainingOverviewTabProps {
  experimentId: string;
  splitBy: string;
  scaffoldFilter: string | undefined;
  languageFilter: string | undefined;
  toolSchemaFilter: string | undefined;
  isActive: boolean;
}

function EmptyChart() {
  return <div className={styles.trainingEmptyChart}>No data available</div>;
}

export default function TrainingOverviewTab({
  experimentId,
  splitBy,
  scaffoldFilter,
  languageFilter,
  toolSchemaFilter,
  isActive,
}: TrainingOverviewTabProps) {
  const queryParams = useMemo((): SelectQueryParams => {
    const filters: NonNullable<SelectQueryParams['filters']> = {
      scaffold: scaffoldFilter,
      task_language: languageFilter,
      tool_schema: toolSchemaFilter,
    };
    const splitByArr = splitBy !== 'none' ? [splitBy] : [];
    return { filters, splitBy: splitByArr };
  }, [scaffoldFilter, languageFilter, toolSchemaFilter, splitBy]);

  const groupByField = splitBy !== 'none' ? splitBy : undefined;

  // ── 7 TraceQL view queries ──
  const { data: rewardStatsRows = [], isLoading: rewardLoading } = useTraceQL(
    'reward_stats',
    experimentId,
    queryParams,
    { enabled: isActive }
  );
  const { data: passRateRows = [], isLoading: passRateLoading } = useTraceQL(
    'pass_rate',
    experimentId,
    queryParams,
    { enabled: isActive }
  );
  const { data: tokenStatsRows = [], isLoading: tokenLoading } = useTraceQL(
    'token_stats',
    experimentId,
    queryParams,
    { enabled: isActive }
  );
  const { data: tokensPerRewardRows = [] } = useTraceQL(
    'tokens_per_reward',
    experimentId,
    queryParams,
    { enabled: isActive }
  );
  const { data: ioRatioRows = [] } = useTraceQL('io_tokens_ratio', experimentId, queryParams, {
    enabled: isActive,
  });
  const { data: successTurnsRows = [] } = useTraceQL(
    'success_turns_stats',
    experimentId,
    queryParams,
    { enabled: isActive }
  );
  const { data: durationRows = [] } = useTraceQL('duration_stats', experimentId, queryParams, {
    enabled: isActive,
  });

  const isLoading = rewardLoading || passRateLoading || tokenLoading;

  // ── Baseline (not migratable, keep PromQL) ──
  const { data: passRateBaselineData } = usePromQLMetric(
    'experiment_pass_rate_baseline',
    experimentId,
    undefined,
    { enabled: isActive }
  );

  // ── Reward chart (experiment_reward_stats → mean_reward + reward_std) ──
  const { xData: rewardXData, lines: rewardLines } = useMemo(() => {
    if (rewardStatsRows.length === 0) return { xData: [] as string[], lines: [] };
    const meanSeries = toTimeSeries(rewardStatsRows, 'mean_reward', groupByField);
    const chart = toChartData(meanSeries);
    // Attach std band only in single-series (no groupBy) case
    if (!groupByField && meanSeries.length === 1) {
      const stdSeries = toTimeSeries(rewardStatsRows, 'reward_std');
      if (stdSeries.length > 0) {
        chart.lines[0].stdData = stdSeries[0].points.map(p => p.value);
      }
    }
    return chart;
  }, [rewardStatsRows, groupByField]);

  // ── Pass rate chart (with baseline overlay) ──
  const { xData: passRateXData, lines: passRateLines } = useMemo(() => {
    if (passRateRows.length === 0) return { xData: [] as string[], lines: [] };
    const chart = toChartData(toTimeSeries(passRateRows, 'pass_rate', groupByField), {
      areaOpacity: 0.08,
    });
    if (passRateBaselineData && passRateBaselineData.length > 0) {
      const baselinePts = passRateBaselineData[0].points;
      chart.lines.push({
        name: 'Historical Baseline',
        data: baselinePts.map(p => p.value),
        color: '#888888',
        dashed: true,
      });
    }
    return chart;
  }, [passRateRows, passRateBaselineData, groupByField]);

  // ── Token efficiency chart ──
  const { xData: effXData, lines: tptLines } = useMemo(
    () =>
      tokenStatsRows.length > 0
        ? toChartData(toTimeSeries(tokenStatsRows, 'tokens_per_traj', groupByField))
        : { xData: [] as string[], lines: [] },
    [tokenStatsRows, groupByField]
  );

  // ── Tokens per Reward ──
  const tprLines = useMemo(
    () =>
      tokensPerRewardRows.length > 0
        ? toChartData(toTimeSeries(tokensPerRewardRows, 'tokens_per_reward', groupByField)).lines
        : [],
    [tokensPerRewardRows, groupByField]
  );

  // ── IO Ratio ──
  const { xData: ioXData, lines: ioLines } = useMemo(
    () =>
      ioRatioRows.length > 0
        ? toChartData(toTimeSeries(ioRatioRows, 'io_ratio', groupByField))
        : { xData: [] as string[], lines: [] },
    [ioRatioRows, groupByField]
  );

  // ── Success turns chart ──
  const { xData: successTurnsXData, lines: successTurnsLines } = useMemo(
    () =>
      successTurnsRows.length > 0
        ? toChartData(toTimeSeries(successTurnsRows, 'mean_turns', groupByField))
        : { xData: [] as string[], lines: [] },
    [successTurnsRows, groupByField]
  );

  // ── Duration chart (verify + sandbox two lines) ──
  const { xData: durationXData, lines: durationLines } = useMemo(() => {
    if (durationRows.length === 0) return { xData: [] as string[], lines: [] };
    const verifySeries = toTimeSeries(durationRows, 'verify_duration_ms', groupByField).map(s => ({
      ...s,
      name: groupByField ? `Verify ${s.name}` : 'Verify Duration',
    }));
    const sandboxSeries = toTimeSeries(durationRows, 'sandbox_duration_ms', groupByField).map(
      s => ({ ...s, name: groupByField ? `Sandbox ${s.name}` : 'Sandbox Create' })
    );
    const allSeries = [...verifySeries, ...sandboxSeries];
    return allSeries.length > 0 ? toChartData(allSeries) : { xData: [] as string[], lines: [] };
  }, [durationRows, groupByField]);

  // ── Duration ratio metrics (latest iteration) ──
  const durationRatios = useMemo(() => {
    if (durationRows.length === 0) return { sandboxCreateRatio: 0, verifyRatio: 0 };
    const maxIteration = Math.max(...durationRows.map(r => r.iteration ?? 0));
    const latestRows = durationRows.filter(r => (r.iteration ?? 0) === maxIteration);
    const avg = (field: string) =>
      latestRows.reduce((s, r) => s + ((r[field] as number) ?? 0), 0) / (latestRows.length || 1);
    const meanDuration = avg('total_duration_ms');
    if (meanDuration === 0) return { sandboxCreateRatio: 0, verifyRatio: 0 };
    return {
      sandboxCreateRatio: avg('sandbox_duration_ms') / meanDuration,
      verifyRatio: avg('verify_duration_ms') / meanDuration,
    };
  }, [durationRows]);

  /** Stable ref so TimeSeriesChart memo compares equal when data unchanged (inline fn breaks memo). */
  const formatPassRateAxis = useCallback((v: number) => `${(v * 100).toFixed(2)}%`, []);

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <Spin size="large" />
        <div className={styles.loadingText}>Loading training data...</div>
      </div>
    );
  }

  const showLegend = splitBy !== 'none' && rewardLines.length > 1;

  return (
    <div>
      <div className={styles.chartsGrid}>
        <ChartPanel title="Mean Reward">
          {rewardXData.length > 0 ? (
            <TimeSeriesChart
              xData={rewardXData}
              lines={rewardLines}
              yAxisName="Reward"
              showLegend={showLegend}
              showSigmaTip
            />
          ) : (
            <EmptyChart />
          )}
        </ChartPanel>
        <ChartPanel title="Pass Rate">
          {passRateXData.length > 0 ? (
            <TimeSeriesChart
              xData={passRateXData}
              lines={passRateLines}
              yAxisName="Pass Rate"
              yAxisMax={1}
              yAxisFormatter={formatPassRateAxis}
              showLegend={showLegend}
            />
          ) : (
            <EmptyChart />
          )}
        </ChartPanel>
      </div>

      <div className={styles.efficiencyGrid}>
        <ChartPanel title="Tokens per Trajectory">
          {effXData.length > 0 ? (
            <TimeSeriesChart
              xData={effXData}
              lines={
                tptLines.length > 0
                  ? tptLines
                  : [{ name: 'Tokens/Trajectory', data: [], color: CHART_COLORS[4] }]
              }
              yAxisName="Tokens"
            />
          ) : (
            <EmptyChart />
          )}
        </ChartPanel>
        <ChartPanel title="Token Efficiency (Tokens/Reward)">
          {effXData.length > 0 ? (
            <TimeSeriesChart
              xData={effXData}
              lines={
                tprLines.length > 0
                  ? tprLines
                  : [{ name: 'Tokens/Reward', data: [], color: CHART_COLORS[3] }]
              }
              yAxisName="Tokens/Reward"
            />
          ) : (
            <EmptyChart />
          )}
        </ChartPanel>
        <ChartPanel title="Input/Output Ratio">
          {ioXData.length > 0 ? (
            <TimeSeriesChart xData={ioXData} lines={ioLines} yAxisName="Ratio" />
          ) : (
            <EmptyChart />
          )}
        </ChartPanel>
      </div>

      {/* M2: Success Turns Trend */}
      <div className={styles.chartSection}>
        <ChartPanel title="Success Mean Turns Trend">
          {successTurnsXData.length > 0 ? (
            <TimeSeriesChart
              xData={successTurnsXData}
              lines={successTurnsLines}
              yAxisName="Turns"
            />
          ) : (
            <EmptyChart />
          )}
        </ChartPanel>
      </div>

      {/* M2: Success Turns Distribution */}
      <div className={styles.chartSection}>
        <SuccessTurnsSection
          experimentId={experimentId}
          filterParams={queryParams}
          isActive={isActive}
        />
      </div>

      {/* Training Duration Statistics */}
      <div className={styles.chartSection}>
        <ChartPanel title="Training Duration Statistics">
          <div className={styles.durationStatsContainer}>
            {/* Left: Metric Cards */}
            <div className={styles.durationMetrics}>
              <MetricCard
                title="Sandbox Create Ratio"
                value={`${(durationRatios.sandboxCreateRatio * 100).toFixed(2)}%`}
              />
              <MetricCard
                title="Verify Ratio"
                value={`${(durationRatios.verifyRatio * 100).toFixed(2)}%`}
              />
            </div>
            {/* Right: Duration Chart */}
            <div className={styles.durationChart}>
              {durationXData.length > 0 ? (
                <TimeSeriesChart
                  xData={durationXData}
                  lines={durationLines}
                  yAxisName="Duration (ms)"
                  showLegend
                />
              ) : (
                <EmptyChart />
              )}
            </div>
          </div>
        </ChartPanel>
      </div>

      {/* Scaffold Stats & Turn Analysis */}
      <div className={styles.chartSection}>
        <ScaffoldStatsSection experimentId={experimentId} isActive={isActive} />
      </div>
      {/* Turn Analysis now uses PromQL metrics internally */}
      <div className={styles.chartSection}>
        <TurnAnalysisSection experimentId={experimentId} isActive={isActive} />
      </div>
    </div>
  );
}
