import { useMemo, useCallback } from 'react';
import { Table, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useNavigate, useParams } from 'react-router-dom';
import { colors, fontSize } from '../../styles/theme';
import type {
  TaskEffectivenessResponse,
  TaskEffectivenessItem,
  TaskClassification,
} from '../../types';
import { formatPct } from '../../utils/format';

interface Props {
  data: TaskEffectivenessResponse;
}

const CLASSIFICATION_CONFIG: Record<
  TaskClassification,
  { label: string; color: string; chartColor: string }
> = {
  all_pass: { label: 'All Passed', color: '#22C55E', chartColor: '#22C55E' },
  all_fail: { label: 'All Failed', color: '#EF4444', chartColor: '#EF4444' },
  mixed: { label: 'Mixed', color: '#F59E0B', chartColor: '#F59E0B' },
  unverified: { label: 'Unverified', color: '#6B7280', chartColor: '#6B7280' },
};

export default function TaskEffectivenessSection({ data }: Props) {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  // ── Filtered & sorted tasks ──
  const filteredTasks = useMemo(() => {
    return [...data.tasks].sort((a, b) => a.pass_rate - b.pass_rate);
  }, [data.tasks]);

  // Handle row click → navigate to rollout explorer with task_id query param
  const handleRowClick = useCallback(
    (taskId: string) => {
      if (id) {
        navigate(`/experiments/${id}/trajectories?task_id=${taskId}`);
      }
    },
    [navigate, id]
  );

  const columns: ColumnsType<TaskEffectivenessItem> = [
    { title: 'Task ID', dataIndex: 'task_id', key: 'task_id', ellipsis: true, width: 180 },
    { title: 'Lang', dataIndex: 'language', key: 'language', width: 80 },
    {
      title: 'Trajectories',
      dataIndex: 'rollout_count',
      key: 'rollout_count',
      width: 100,
      sorter: (a, b) => a.rollout_count - b.rollout_count,
    },
    {
      title: 'Valid',
      dataIndex: 'valid_count',
      key: 'valid_count',
      width: 90,
      sorter: (a, b) => a.valid_count - b.valid_count,
    },
    {
      title: 'Pass',
      dataIndex: 'pass_count',
      key: 'pass_count',
      width: 90,
      sorter: (a, b) => a.pass_count - b.pass_count,
    },
    {
      title: 'Fail',
      dataIndex: 'fail_count',
      key: 'fail_count',
      width: 80,
      sorter: (a, b) => a.fail_count - b.fail_count,
    },
    {
      title: 'Pass%',
      dataIndex: 'pass_rate',
      key: 'pass_rate',
      width: 90,
      defaultSortOrder: 'ascend',
      sorter: (a, b) => a.pass_rate - b.pass_rate,
      render: (v: number) => (
        <span
          className="font-mono"
          style={{ color: v < 0.3 ? colors.error : v < 0.7 ? colors.warning : colors.success }}
        >
          {formatPct(v)}
        </span>
      ),
    },
    {
      title: '1st Pass Iter#',
      dataIndex: 'first_pass_iteration',
      key: 'first_pass_iteration',
      width: 110,
      render: (v: number | null) => <span className="font-mono">{v === null ? '—' : `#${v}`}</span>,
      sorter: (a, b) => (a.first_pass_iteration ?? Infinity) - (b.first_pass_iteration ?? Infinity),
    },
    {
      title: 'Pass Type',
      dataIndex: 'classification',
      key: 'classification',
      width: 100,
      render: (v: TaskClassification) => {
        const cfg = CLASSIFICATION_CONFIG[v];
        return (
          <Tag color={cfg.color} style={{ margin: 0 }}>
            {cfg.label}
          </Tag>
        );
      },
      filters: Object.entries(CLASSIFICATION_CONFIG).map(([k, v]) => ({ text: v.label, value: k })),
      onFilter: (value, record) => record.classification === value,
    },
  ];

  return (
    <div
      style={{
        backgroundColor: colors.panelBg,
        border: `1px solid ${colors.borderSecondary}`,
        borderRadius: 8,
        padding: 16,
        overflow: 'auto',
      }}
    >
      <div style={{ marginBottom: 8, fontSize: fontSize.bodyCompact, color: colors.textSecondary }}>
        Task Details
        {' · '}Click row to open Trajectory Explorer
      </div>
      <Table<TaskEffectivenessItem>
        columns={columns}
        dataSource={filteredTasks}
        rowKey="task_id"
        size="small"
        pagination={{ pageSize: 15, showSizeChanger: false }}
        scroll={{ x: 1000 }}
        onRow={record => ({
          onClick: () => handleRowClick(record.task_id),
          style: { cursor: 'pointer' },
        })}
      />
    </div>
  );
}
