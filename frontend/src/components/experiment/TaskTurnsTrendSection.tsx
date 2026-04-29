import { useMemo, useState, useEffect } from 'react';
import { Select, Spin, Space } from 'antd';
import ChartPanel from '../shared/ChartPanel';
import TimeSeriesChart from '../charts/TimeSeriesChart';
import { useTaskTurnsTrend } from '../../hooks/useTaskTurnsTrend';
import { toChartData } from '../../pages/experiment-detail/helpers';
import type { AnalysisFilterParams } from '../../api/stats';

const DEFAULT_TOP_N = 10;

interface TaskTurnsTrendSectionProps {
  experimentId: string;
  filterParams?: AnalysisFilterParams;
  isActive: boolean;
}

export default function TaskTurnsTrendSection({
  experimentId,
  filterParams,
  isActive,
}: TaskTurnsTrendSectionProps) {
  const { allSeries, rankedTasks, isLoading } = useTaskTurnsTrend(experimentId, filterParams, {
    enabled: isActive,
  });

  const [selectedTasks, setSelectedTasks] = useState<string[]>([]);

  useEffect(() => {
    if (rankedTasks.length > 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelectedTasks(rankedTasks.slice(0, DEFAULT_TOP_N).map(t => t.taskId));
    }
  }, [rankedTasks]);

  const taskOptions = useMemo(
    () => rankedTasks.map(t => ({ label: t.taskId, value: t.taskId })),
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
      <ChartPanel title="Task Turns Trend">
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <Spin />
        </div>
      </ChartPanel>
    );
  }

  if (allSeries.length === 0) {
    return (
      <ChartPanel title="Task Turns Trend">
        <div style={{ textAlign: 'center', padding: 40, opacity: 0.5 }}>
          No iteration data available
        </div>
      </ChartPanel>
    );
  }

  return (
    <ChartPanel title="Task Turns Trend" extra={selectorExtra}>
      <TimeSeriesChart xData={xData} lines={lines} yAxisName="Avg Turns" showLegend height={360} />
    </ChartPanel>
  );
}
