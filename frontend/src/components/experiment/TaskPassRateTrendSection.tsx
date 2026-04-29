import { useMemo, useState, useEffect } from 'react';
import { Select, Spin, Space } from 'antd';
import ChartPanel from '../shared/ChartPanel';
import TimeSeriesChart from '../charts/TimeSeriesChart';
import { useTaskPassRateTrend } from '../../hooks/useTaskPassRateTrend';
import { toChartData } from '../../pages/experiment-detail/helpers';
import type { AnalysisFilterParams } from '../../api/stats';

const DEFAULT_TOP_N = 10;

interface TaskPassRateTrendSectionProps {
  experimentId: string;
  filterParams?: AnalysisFilterParams;
  isActive: boolean;
}

export default function TaskPassRateTrendSection({
  experimentId,
  filterParams,
  isActive,
}: TaskPassRateTrendSectionProps) {
  const { allSeries, rankedTasks, isLoading } = useTaskPassRateTrend(experimentId, filterParams, {
    enabled: isActive,
  });

  const [selectedTasks, setSelectedTasks] = useState<string[]>([]);

  // Auto-select top N tasks when data first loads or changes
  useEffect(() => {
    if (rankedTasks.length > 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelectedTasks(rankedTasks.slice(0, DEFAULT_TOP_N).map(t => t.taskId));
    }
  }, [rankedTasks]);

  const taskOptions = useMemo(
    () =>
      rankedTasks.map(t => ({
        label: t.taskId,
        value: t.taskId,
      })),
    [rankedTasks]
  );

  const selectedSeries = useMemo(
    () => allSeries.filter(s => selectedTasks.includes(s.name)),
    [allSeries, selectedTasks]
  );

  const { xData, lines } = useMemo(
    () => toChartData(selectedSeries, { areaOpacity: 0 }),
    [selectedSeries]
  );

  const selectorExtra = (
    <Space size={8}>
      <span style={{ fontSize: 12, opacity: 0.6 }}>Tasks:</span>
      <Select
        mode="multiple"
        size="small"
        value={selectedTasks}
        onChange={setSelectedTasks}
        options={taskOptions}
        style={{ minWidth: 200, maxWidth: 480 }}
        maxTagCount={3}
        maxTagTextLength={12}
        placeholder="Select tasks"
        allowClear
        showSearch
        optionFilterProp="label"
      />
    </Space>
  );

  if (isLoading) {
    return (
      <ChartPanel title="Task Pass Rate Trend">
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <Spin />
        </div>
      </ChartPanel>
    );
  }

  if (allSeries.length === 0) {
    return (
      <ChartPanel title="Task Pass Rate Trend">
        <div style={{ textAlign: 'center', padding: 40, opacity: 0.5 }}>
          No iteration data available
        </div>
      </ChartPanel>
    );
  }

  return (
    <ChartPanel title="Task Pass Rate Trend" extra={selectorExtra}>
      <TimeSeriesChart
        xData={xData}
        lines={lines}
        yAxisName="Pass Rate"
        yAxisMax={1}
        yAxisFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
        showLegend
        height={360}
      />
    </ChartPanel>
  );
}
