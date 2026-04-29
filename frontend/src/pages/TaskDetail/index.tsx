import { forwardRef, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';
import { Table } from 'antd';
import type { TableProps } from 'antd';
import OutcomeBadge from '../../components/shared/OutcomeBadge';
import { queryTraceQL } from '../../api/traceql';
import type { TraceQLRow } from '../../api/traceql';
import { buildTaskByExperimentQuery } from '../../queries/task';
import { formatPct } from '../../utils/format';
import styles from './styles.module.css';

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

interface TaskByExperimentRow {
  task_id: string;
  task_language: string;
  experiment_id: string;
  trajectory_count: number;
  pass_count: number;
  fail_count: number;
  pass_rate: number;
  max_turns: number;
  min_turns: number;
  avg_turns: number;
  max_duration_ms: number;
  min_duration_ms: number;
  avg_duration_ms: number;
}

const TableBodyCell = forwardRef<
  HTMLTableCellElement,
  React.TdHTMLAttributes<HTMLTableCellElement>
>(({ className, ...rest }, ref) => (
  <td ref={ref} {...rest} className={clsx(styles.dataCell, className)} />
));
TableBodyCell.displayName = 'TableBodyCell';

const tableComponents: TableProps<TaskByExperimentRow>['components'] = {
  body: { cell: TableBodyCell },
};

function toTaskByExperimentRow(row: TraceQLRow): TaskByExperimentRow {
  return {
    task_id: String(row.task_id ?? ''),
    task_language: String(row.task_language ?? ''),
    experiment_id: String(row.experiment_id ?? ''),
    trajectory_count: Number(row.trajectory_count ?? 0),
    pass_count: Number(row.pass_count ?? 0),
    fail_count: Number(row.fail_count ?? 0),
    pass_rate: Number(row.pass_rate ?? 0),
    max_turns: Number(row.max_turns ?? 0),
    min_turns: Number(row.min_turns ?? 0),
    avg_turns: Number(row.avg_turns ?? 0),
    max_duration_ms: Number(row.max_duration_ms ?? 0),
    min_duration_ms: Number(row.min_duration_ms ?? 0),
    avg_duration_ms: Number(row.avg_duration_ms ?? 0),
  };
}

export default function TaskDetail() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const { data: rows = [], isLoading } = useQuery({
    queryKey: ['task-by-experiment', taskId],
    queryFn: () =>
      queryTraceQL(buildTaskByExperimentQuery(taskId!)).then(r =>
        r.filter(row => row.experiment_id).map(toTaskByExperimentRow)
      ),
    enabled: !!taskId,
    staleTime: 60_000,
  });

  const expandedList = useMemo(
    () => [...rows].sort((a, b) => b.trajectory_count - a.trajectory_count),
    [rows]
  );

  const columns: TableProps<TaskByExperimentRow>['columns'] = useMemo(
    () => [
      {
        title: 'Task ID',
        dataIndex: 'task_id',
        key: 'task_id',
        width: 180,
        render: (v: string) => (
          <span className="inline-block max-w-[180px] truncate font-mono text-sm" title={v}>
            {v}
          </span>
        ),
      },
      {
        title: 'Language',
        dataIndex: 'task_language',
        key: 'task_language',
        width: 90,
        render: (v: string) => <span>{v || '-'}</span>,
      },
      {
        title: 'Experiment ID',
        dataIndex: 'experiment_id',
        key: 'experiment_id',
        width: 200,
        render: (v: string) => (
          <span className="inline-block max-w-[200px] truncate font-mono text-sm" title={v || '-'}>
            {v || '-'}
          </span>
        ),
      },
      {
        title: 'Trajectories',
        dataIndex: 'trajectory_count',
        key: 'trajectory_count',
        width: 110,
        render: (v: number) => <span className="font-medium text-text-primary">{v}</span>,
        sorter: true,
      },
      {
        title: 'Pass Rate',
        dataIndex: 'pass_rate',
        key: 'pass_rate',
        width: 100,
        sorter: true,
        render: (v: number) => {
          if (v === undefined || v === null) return '-';
          return (
            <span
              className={clsx('text-sm font-medium tabular-nums', {
                'text-success': v >= 0.8,
                'text-warning': v < 0.8 && v >= 0.5,
                'text-failure': v < 0.5,
              })}
            >
              {formatPct(v)}
            </span>
          );
        },
      },
      {
        title: 'Outcome',
        key: 'outcome_breakdown',
        width: 160,
        render: (_: unknown, record: TaskByExperimentRow) => (
          <span className="flex items-center gap-1.5">
            <OutcomeBadge outcome="success" />
            <span className="text-sm">{record.pass_count}</span>
            <OutcomeBadge outcome="failure" />
            <span className="text-sm">{record.fail_count}</span>
          </span>
        ),
      },
      {
        title: 'Max Turns',
        dataIndex: 'max_turns',
        key: 'max_turns',
        width: 90,
        sorter: true,
      },
      {
        title: 'Min Turns',
        dataIndex: 'min_turns',
        key: 'min_turns',
        width: 90,
        sorter: true,
      },
      {
        title: 'Max Duration',
        dataIndex: 'max_duration_ms',
        key: 'max_duration_ms',
        width: 110,
        render: (v: number) => formatDuration(v),
        sorter: true,
      },
      {
        title: 'Min Duration',
        dataIndex: 'min_duration_ms',
        key: 'min_duration_ms',
        width: 110,
        render: (v: number) => formatDuration(v),
        sorter: true,
      },
      {
        title: 'Avg Turns',
        dataIndex: 'avg_turns',
        key: 'avg_turns',
        width: 90,
        render: (v: number) => v.toFixed(1),
        sorter: true,
      },
      {
        title: 'Avg Duration',
        dataIndex: 'avg_duration_ms',
        key: 'avg_duration_ms',
        width: 110,
        render: (v: number) => formatDuration(v),
        sorter: true,
      },
    ],
    []
  );

  return (
    <div className="px-6 py-5">
      <h1 className="mb-5 text-lg font-semibold text-text-primary">Task Detail</h1>

      <Table<TaskByExperimentRow>
        bordered
        components={tableComponents}
        dataSource={expandedList}
        columns={columns}
        rowKey={record => `${record.task_id}::${record.experiment_id}`}
        loading={isLoading}
        scroll={{ x: 1250 }}
        pagination={false}
        onRow={record => ({
          onClick: () => {
            navigate(`/tasks/${taskId}/trajectories?experiment_id=${record.experiment_id}`);
          },
          className: 'cursor-pointer',
        })}
      />
    </div>
  );
}
