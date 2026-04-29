import { useMemo } from 'react';
import { Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { colors } from '../../styles/theme';
import { useTraceQL } from '../../hooks/useTraceQL';
import { formatDuration, formatPct } from '../../utils/format';
import ChartPanel from '../shared/ChartPanel';

interface Props {
  experimentId: string;
  isActive?: boolean;
}

interface ScaffoldStatsItem {
  scaffold: string;
  count: number;
  passed: number;
  pass_rate: number;
  avg_reward: number;
  avg_turns: number;
  avg_tokens: number;
  avg_duration_ms: number;
}

const SCAFFOLD_PARAMS = { splitBy: ['scaffold'], omitIterationGroupBy: true };

export default function ScaffoldStatsSection({ experimentId, isActive = true }: Props) {
  const { data: rows = [], isLoading } = useTraceQL(
    'scaffold_stats',
    experimentId,
    SCAFFOLD_PARAMS,
    {
      enabled: isActive,
    }
  );

  const scaffoldData = useMemo<ScaffoldStatsItem[]>(() => {
    if (rows.length === 0) return [];

    return rows.map(row => {
      const count = row.trajectory_count ?? 0;
      const rate = row.pass_rate ?? 0;
      return {
        scaffold: String(row.scaffold ?? 'unknown'),
        count,
        passed: Math.round(count * rate),
        pass_rate: rate,
        avg_reward: row.mean_reward ?? 0,
        avg_turns: row.mean_turns ?? 0,
        avg_tokens: row.tokens_per_traj ?? 0,
        avg_duration_ms: row.total_duration_ms ?? 0,
      };
    });
  }, [rows]);

  // Calculate totals for summary row
  const dataWithTotal = useMemo(() => {
    if (scaffoldData.length === 0) return [];
    const totalCount = scaffoldData.reduce((s, d) => s + d.count, 0);
    const totalPassed = scaffoldData.reduce((s, d) => s + d.passed, 0);
    const total: ScaffoldStatsItem = {
      scaffold: 'Total',
      count: totalCount,
      passed: totalPassed,
      pass_rate: totalCount > 0 ? totalPassed / totalCount : 0,
      avg_reward:
        totalCount > 0
          ? scaffoldData.reduce((s, d) => s + d.avg_reward * d.count, 0) / totalCount
          : 0,
      avg_turns:
        totalCount > 0
          ? scaffoldData.reduce((s, d) => s + d.avg_turns * d.count, 0) / totalCount
          : 0,
      avg_tokens:
        totalCount > 0
          ? scaffoldData.reduce((s, d) => s + d.avg_tokens * d.count, 0) / totalCount
          : 0,
      avg_duration_ms:
        totalCount > 0
          ? scaffoldData.reduce((s, d) => s + d.avg_duration_ms * d.count, 0) / totalCount
          : 0,
    };
    return [...scaffoldData, total];
  }, [scaffoldData]);

  const columns: ColumnsType<ScaffoldStatsItem> = [
    {
      title: 'Scaffold',
      dataIndex: 'scaffold',
      key: 'scaffold',
      width: 140,
      render: (v: string) => <span style={{ fontWeight: v === 'Total' ? 700 : 400 }}>{v}</span>,
    },
    {
      title: 'Trajectories',
      dataIndex: 'count',
      key: 'count',
      width: 80,
      sorter: (a, b) => {
        if (a.scaffold === 'Total') return 1;
        if (b.scaffold === 'Total') return -1;
        return a.count - b.count;
      },
      render: (v: number) => <span className="font-mono">{v}</span>,
    },
    {
      title: 'Passed',
      dataIndex: 'passed',
      key: 'passed',
      width: 80,
      sorter: (a, b) => {
        if (a.scaffold === 'Total') return 1;
        if (b.scaffold === 'Total') return -1;
        return a.passed - b.passed;
      },
      render: (v: number) => <span className="font-mono">{v}</span>,
    },
    {
      title: 'Pass%',
      dataIndex: 'pass_rate',
      key: 'pass_rate',
      width: 100,
      sorter: (a, b) => {
        if (a.scaffold === 'Total') return 1;
        if (b.scaffold === 'Total') return -1;
        return a.pass_rate - b.pass_rate;
      },
      render: (v: number) => (
        <span
          className="font-mono"
          style={{ color: v < 0.5 ? colors.error : v < 0.8 ? colors.warning : colors.success }}
        >
          {formatPct(v)}
        </span>
      ),
    },
    {
      title: 'AvgReward',
      dataIndex: 'avg_reward',
      key: 'avg_reward',
      width: 100,
      sorter: (a, b) => {
        if (a.scaffold === 'Total') return 1;
        if (b.scaffold === 'Total') return -1;
        return a.avg_reward - b.avg_reward;
      },
      render: (v: number) => <span className="font-mono">{v.toFixed(2)}</span>,
    },
    {
      title: 'AvgTurns',
      dataIndex: 'avg_turns',
      key: 'avg_turns',
      width: 100,
      sorter: (a, b) => {
        if (a.scaffold === 'Total') return 1;
        if (b.scaffold === 'Total') return -1;
        return a.avg_turns - b.avg_turns;
      },
      render: (v: number) => <span className="font-mono">{v.toFixed(2)}</span>,
    },
    {
      title: 'AvgTokens',
      dataIndex: 'avg_tokens',
      key: 'avg_tokens',
      width: 100,
      sorter: (a, b) => {
        if (a.scaffold === 'Total') return 1;
        if (b.scaffold === 'Total') return -1;
        return a.avg_tokens - b.avg_tokens;
      },
      render: (v: number) => <span className="font-mono">{v.toFixed(0)}</span>,
    },
    {
      title: 'AvgDuration',
      dataIndex: 'avg_duration_ms',
      key: 'avg_duration_ms',
      width: 120,
      sorter: (a, b) => {
        if (a.scaffold === 'Total') return 1;
        if (b.scaffold === 'Total') return -1;
        return a.avg_duration_ms - b.avg_duration_ms;
      },
      render: (v: number) => <span className="font-mono">{formatDuration(v)}</span>,
    },
  ];

  if (isLoading) {
    return (
      <ChartPanel title="Scaffold Stats">
        <div style={{ textAlign: 'center', color: colors.textTertiary }}>
          Loading scaffold stats...
        </div>
      </ChartPanel>
    );
  }

  if (scaffoldData.length === 0) {
    return (
      <ChartPanel title="Scaffold Stats">
        <div style={{ textAlign: 'center', color: colors.textTertiary }}>
          No scaffold data available
        </div>
      </ChartPanel>
    );
  }

  return (
    <ChartPanel title="Scaffold Stats">
      <Table<ScaffoldStatsItem>
        columns={columns}
        dataSource={dataWithTotal}
        rowKey="scaffold"
        size="small"
        pagination={false}
        rowClassName={record => (record.scaffold === 'Total' ? 'summary-row' : '')}
      />
    </ChartPanel>
  );
}
