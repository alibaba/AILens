import { Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import clsx from 'clsx';
import ChartPanel from '../shared/ChartPanel';
import { formatDuration, formatPct } from '../../utils/format';
import { useTraceQL } from '../../hooks/useTraceQL';
import { useMemo } from 'react';

interface Props {
  experimentId: string;
  isActive?: boolean;
}

interface TurnBucket {
  range: string;
  count: number;
  pass_rate: number;
  max_duration_passed_ms: number;
  avg_duration_passed_ms: number;
}

export default function TurnAnalysisSection({ experimentId, isActive = true }: Props) {
  const { data: rows = [] } = useTraceQL(
    'turns_distribution',
    experimentId,
    { omitIterationGroupBy: true },
    { enabled: isActive }
  );

  const tableData = useMemo((): TurnBucket[] => {
    if (rows.length === 0) return [];

    return rows
      .map(row => ({
        range: String(row.turns ?? ''),
        count: row.total_count ?? 0,
        pass_rate:
          (row.total_count ?? 0) > 0 ? (row.passed_count ?? 0) / (row.total_count ?? 0) : 0,
        max_duration_passed_ms: row.max_duration_ms ?? 0,
        avg_duration_passed_ms:
          (row.total_count ?? 0) > 0 ? (row.sum_duration_ms ?? 0) / (row.total_count ?? 0) : 0,
      }))
      .sort((a, b) => parseInt(a.range) - parseInt(b.range));
  }, [rows]);

  const columns: ColumnsType<TurnBucket> = [
    { title: 'Turns', dataIndex: 'range', key: 'range', width: 80 },
    { title: 'Trajectories', dataIndex: 'count', key: 'count', width: 80 },
    {
      title: 'Pass%',
      dataIndex: 'pass_rate',
      key: 'pass_rate',
      width: 100,
      render: (v: number) => (
        <span
          className={clsx('tabular-nums', {
            'text-success': v >= 0.8,
            'text-warning': v < 0.8 && v >= 0.5,
            'text-failure': v < 0.5,
          })}
        >
          {formatPct(v)}
        </span>
      ),
    },
    {
      title: 'MaxDuration(passed)',
      dataIndex: 'max_duration_passed_ms',
      key: 'max_duration_passed_ms',
      width: 160,
      render: (v: number) => formatDuration(v),
    },
    {
      title: 'AvgDuration(passed)',
      dataIndex: 'avg_duration_passed_ms',
      key: 'avg_duration_passed_ms',
      width: 160,
      render: (v: number) => formatDuration(v),
    },
  ];

  return (
    <div>
      <ChartPanel title="Turn Distribution">
        <Table<TurnBucket>
          columns={columns}
          dataSource={tableData}
          rowKey="range"
          size="small"
          pagination={false}
        />
      </ChartPanel>
    </div>
  );
}
