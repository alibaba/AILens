import { useMemo, useState, useCallback } from 'react';
import clsx from 'clsx';
import { useNavigate, useParams, useLocation, useSearchParams } from 'react-router-dom';
import { Table, Select, InputNumber, Space, Spin, Tag } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useTaskEffectiveness } from '../../hooks/useTaskEffectiveness';
import type { TaskEffectivenessItem } from '../../types';
import { formatPct } from '../../utils/format';
import styles from './styles.module.css';

export default function TaskExplorer() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();

  // Detect mode: dataset vs experiment
  const isDatasetMode = location.pathname.startsWith('/datasets/');

  const datasetFilter = isDatasetMode ? id : undefined;
  const [languageFilter, setLanguageFilter] = useState<string | undefined>(
    searchParams.get('language') || undefined
  );
  const [passRateMin, setPassRateMin] = useState<number | null>(null);
  const [passRateMax, setPassRateMax] = useState<number | null>(null);
  const [page, setPage] = useState(1);

  // --- Data fetching ---

  // In dataset mode: pass dataset_name filter, empty experimentId
  const extraFilters = useMemo(
    () => (isDatasetMode && id ? { dataset_name: id } : undefined),
    [isDatasetMode, id]
  );

  const { data, isLoading } = useTaskEffectiveness(
    isDatasetMode ? '' : (id ?? ''),
    undefined,
    { enabled: !!id },
    extraFilters
  );

  // --- Derived data ---

  const languageOptions = useMemo(() => {
    const langs = new Set<string>();
    for (const t of data?.tasks ?? []) {
      if (t.language) langs.add(t.language);
    }
    return Array.from(langs)
      .sort()
      .map(l => ({ label: l, value: l }));
  }, [data]);

  const filteredTasks = useMemo(() => {
    const tasks = data?.tasks ?? [];
    return tasks.filter(t => {
      if (datasetFilter && t.dataset_name !== datasetFilter) return false;
      if (languageFilter && t.language !== languageFilter) return false;
      const pct = t.pass_rate * 100;
      if (passRateMin !== null && pct < passRateMin) return false;
      if (passRateMax !== null && pct > passRateMax) return false;
      return true;
    });
  }, [data, datasetFilter, languageFilter, passRateMin, passRateMax]);

  const summaryStats = useMemo(() => {
    let trajectoryTotal = 0;
    let passTotal = 0;
    let failTotal = 0;
    for (const t of filteredTasks) {
      trajectoryTotal += t.rollout_count;
      passTotal += t.pass_count;
      failTotal += t.fail_count;
    }
    return { taskCount: filteredTasks.length, trajectoryTotal, passTotal, failTotal };
  }, [filteredTasks]);

  // --- Filter change handlers ---

  const resetPage = useCallback(() => setPage(1), []);

  const handleLanguageChange = useCallback(
    (v: string | undefined) => {
      setLanguageFilter(v);
      resetPage();
    },
    [resetPage]
  );
  const handlePassRateMinChange = useCallback(
    (v: number | null) => {
      setPassRateMin(v);
      resetPage();
    },
    [resetPage]
  );
  const handlePassRateMaxChange = useCallback(
    (v: number | null) => {
      setPassRateMax(v);
      resetPage();
    },
    [resetPage]
  );

  // --- Table columns: Task ID, Dataset, Experiment ID, Scaffold, Tool Schema, Trajectories, Pass, Fail, Pass Rate ---

  const columns = useMemo<ColumnsType<TaskEffectivenessItem>>(
    () => [
      {
        title: 'Task ID',
        dataIndex: 'task_id',
        width: 180,
        sorter: (a, b) => a.task_id.localeCompare(b.task_id),
        render: (v: string) => (
          <span
            className={clsx('font-mono', styles.monoCell, 'inline-block max-w-[160px] truncate')}
            title={v}
          >
            {v}
          </span>
        ),
      },
      {
        title: 'Language',
        dataIndex: 'language',
        key: 'language',
        width: 100,
        sorter: (a: TaskEffectivenessItem, b: TaskEffectivenessItem) =>
          a.language.localeCompare(b.language),
        render: (v: string) => (v ? <Tag>{v}</Tag> : <span className="text-text-disabled">-</span>),
      },
      {
        title: 'Dataset',
        dataIndex: 'dataset_name',
        key: 'dataset_name',
        width: 140,
        sorter: (a: TaskEffectivenessItem, b: TaskEffectivenessItem) =>
          a.dataset_name.localeCompare(b.dataset_name),
        render: (v: string) => (
          <span className={clsx('font-mono', styles.monoCell)}>{v || '-'}</span>
        ),
      },
      {
        title: 'Trajectories',
        dataIndex: 'rollout_count',
        width: 110,
        sorter: (a: TaskEffectivenessItem, b: TaskEffectivenessItem) =>
          a.rollout_count - b.rollout_count,
        render: (v: number) => <span className="font-mono">{v.toLocaleString()}</span>,
      },
      {
        title: 'Pass',
        dataIndex: 'pass_count',
        width: 80,
        sorter: (a: TaskEffectivenessItem, b: TaskEffectivenessItem) => a.pass_count - b.pass_count,
        render: (v: number) => (
          <span>
            <CheckCircleOutlined className="mr-1 text-success" />
            {v}
          </span>
        ),
      },
      {
        title: 'Fail',
        dataIndex: 'fail_count',
        width: 80,
        sorter: (a: TaskEffectivenessItem, b: TaskEffectivenessItem) => a.fail_count - b.fail_count,
        render: (v: number) => (
          <span>
            <CloseCircleOutlined className="mr-1 text-failure" />
            {v}
          </span>
        ),
      },
      {
        title: 'Pass Rate',
        dataIndex: 'pass_rate',
        width: 100,
        sorter: (a: TaskEffectivenessItem, b: TaskEffectivenessItem) => a.pass_rate - b.pass_rate,
        defaultSortOrder: 'ascend' as const,
        render: (v: number) => (
          <span
            className={clsx(
              'font-mono',
              v >= 0.7 && 'text-success',
              v < 0.7 && v >= 0.4 && 'text-warning',
              v < 0.4 && 'text-failure'
            )}
          >
            {formatPct(v)}
          </span>
        ),
      },
    ],
    []
  );

  // --- Row click handler ---

  const handleRowClick = useCallback(
    (record: TaskEffectivenessItem) => {
      const params = new URLSearchParams({ task: record.task_id });
      if (record.language) params.set('language', record.language);
      const qs = params.toString();
      if (isDatasetMode) {
        navigate(`/datasets/${encodeURIComponent(id!)}/trajectories?${qs}`);
      } else {
        navigate(`/experiments/${id}/trajectories?${qs}`);
      }
    },
    [isDatasetMode, id, navigate]
  );

  // --- Render ---

  if (!id) {
    return (
      <div className={styles.container}>
        <div className={styles.errorBanner}>Select a project to view experiments.</div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Filter Bar */}
      <div className={styles.filterBar}>
        <Space size={4}>
          <span className={styles.filterLabel}>Language</span>
          <Select
            value={languageFilter}
            onChange={handleLanguageChange}
            allowClear
            placeholder="All"
            className="w-[120px]"
            size="small"
            options={languageOptions}
          />
        </Space>

        <Space size={4}>
          <span className={styles.filterLabel}>Pass Rate</span>
          <InputNumber
            value={passRateMin}
            onChange={handlePassRateMinChange}
            min={0}
            max={100}
            step={1}
            placeholder="Min"
            addonAfter="%"
            size="small"
            className="w-[100px]"
          />
          <span className={styles.filterDash}>–</span>
          <InputNumber
            value={passRateMax}
            onChange={handlePassRateMaxChange}
            min={0}
            max={100}
            step={1}
            placeholder="Max"
            addonAfter="%"
            size="small"
            className="w-[100px]"
          />
        </Space>
      </div>

      {/* Summary Bar */}
      <div className={styles.summaryBar}>
        <span>
          <span className={styles.summaryCount}>{summaryStats.taskCount}</span> tasks
        </span>
        <span>
          <span className={styles.summaryCount}>
            {summaryStats.trajectoryTotal.toLocaleString()}
          </span>{' '}
          trajectories
        </span>
        <span>
          <CheckCircleOutlined className="mr-1 text-success" />
          <span className={styles.summaryCount}>{summaryStats.passTotal.toLocaleString()}</span>
        </span>
        <span>
          <CloseCircleOutlined className="mr-1 text-failure" />
          <span className={styles.summaryCount}>{summaryStats.failTotal.toLocaleString()}</span>
        </span>
        {isLoading && <Spin size="small" />}
      </div>

      {/* Tasks Table */}
      <Table<TaskEffectivenessItem>
        dataSource={filteredTasks}
        columns={columns}
        rowKey={r => `${r.task_id}__${r.dataset_name}__${r.language}`}
        loading={isLoading}
        size="small"
        pagination={{
          current: page,
          pageSize: 50,
          total: filteredTasks.length,
          showSizeChanger: false,
          showTotal: (total, range) => `${range[0]}-${range[1]} of ${total}`,
          size: 'small',
        }}
        onChange={pagination => setPage(pagination.current ?? 1)}
        onRow={record => ({
          onClick: () => handleRowClick(record),
          className: 'cursor-pointer',
        })}
        className={styles.tasksTable}
      />
    </div>
  );
}
