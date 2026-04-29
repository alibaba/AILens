import { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { Spin } from 'antd';
import ChartPanel from '../shared/ChartPanel';
import { useTaskEffectiveness } from '../../hooks/useTaskEffectiveness';
import { mergeChartOption } from '../../styles/echarts-dark';
import { colors, fontSize } from '../../styles/theme';
import type { AnalysisFilterParams } from '../../api/stats';
import type { TaskClassification } from '../../types';

const CLASSIFICATION_CONFIG: Record<TaskClassification, { label: string; color: string }> = {
  all_pass: { label: 'All Passed', color: '#22C55E' },
  all_fail: { label: 'All Failed', color: '#EF4444' },
  mixed: { label: 'Mixed', color: '#F59E0B' },
  unverified: { label: 'Unverified', color: '#6B7280' },
};

interface TaskDifficultySectionProps {
  experimentId: string;
  filterParams?: AnalysisFilterParams;
  isActive: boolean;
}

export default function TaskDifficultySection({
  experimentId,
  filterParams,
  isActive,
}: TaskDifficultySectionProps) {
  const { data, isLoading } = useTaskEffectiveness(experimentId, filterParams, {
    enabled: isActive,
  });

  const option = useMemo(() => {
    if (!data) return null;
    const { summary } = data;

    const pieData = (
      Object.entries(CLASSIFICATION_CONFIG) as [
        TaskClassification,
        { label: string; color: string },
      ][]
    )
      .map(([key, cfg]) => ({
        name: cfg.label,
        value: summary[key],
        itemStyle: { color: cfg.color },
      }))
      .filter(d => d.value > 0);

    return mergeChartOption({
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '50%'],
          avoidLabelOverlap: true,
          label: {
            show: true,
            formatter: '{b}: {c} ({d}%)',
            color: colors.textPrimary,
            fontSize: fontSize.sm,
          },
          emphasis: {
            label: {
              show: true,
              fontSize: fontSize.sm,
              fontWeight: 'bold',
              color: colors.textPrimary,
            },
          },
          labelLayout: { hideOverlap: true },
          data: pieData,
        },
      ],
    });
  }, [data]);

  if (isLoading) {
    return (
      <ChartPanel title="Task Difficulty Distribution">
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <Spin />
        </div>
      </ChartPanel>
    );
  }

  if (!option) {
    return (
      <ChartPanel title="Task Difficulty Distribution">
        <div style={{ textAlign: 'center', padding: 40, opacity: 0.5 }}>No task data available</div>
      </ChartPanel>
    );
  }

  return (
    <ChartPanel title="Task Difficulty Distribution">
      <ReactECharts option={option} style={{ height: 250 }} opts={{ renderer: 'svg' }} />
    </ChartPanel>
  );
}
