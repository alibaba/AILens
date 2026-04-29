import { useMemo, useState, useCallback, useEffect } from 'react';
import clsx from 'clsx';
import { useParams, useSearchParams, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Table, Select, InputNumber, Space, Spin, Form, Drawer, Button, Tooltip, Tag } from 'antd';
import { UpOutlined, DownOutlined } from '@ant-design/icons';
import type { TableProps, TablePaginationConfig } from 'antd';
import type { FilterValue, SorterResult } from 'antd/es/table/interface';
import OutcomeBadge from '../../components/shared/OutcomeBadge';
import { queryTraceQL } from '../../api/traceql';
import type { TraceQLRow } from '../../api/traceql';
import { buildTrajectoryListQuery, buildOutcomeStatsQuery } from '../../queries/trajectory';
import { TrajectoryViewerPanel } from '../TrajectoryViewer';
import { formatPct } from '../../utils/format';
import type { OutcomeType } from '../../types';
import styles from './styles.module.css';

/** Select "All" sentinel — never send to TraceQL. */
const FILTER_ALL = '__all__' as const;

// ── Types ──

interface FilterFormValues {
  experiment: string;
  outcome: string[];
  iteration: string;
  language: string;
  rewardMin: number | null;
  rewardMax: number | null;
  turnsMin: number | null;
  turnsMax: number | null;
  taskId: string | undefined;
}

interface TrajectoryItem {
  id: string;
  experiment_id: string;
  iteration_id: string;
  iteration_num: number;
  task_id: string;
  task_language: string;
  scaffold: string;
  tool_schema: string;
  outcome: 'success' | 'failure' | 'timeout' | 'error';
  reward: number;
  reward_components: Record<string, number>;
  passed: boolean;
  total_turns: number;
  total_events: number;
  duration_ms: number;
  total_tokens: number;
  input_tokens: number;
  output_tokens: number;
  tool_call_count: number;
  tool_success_rate: number;
  repeat_action_rate: number;
  error_turn_count: number;
  first_error_turn: number;
  llm_time_ratio: number;
  tokens_per_turn: number;
  otel_trace_id: string;
  annotation_count: number;
  created_at: string;
}

interface TrajectoriesResponse {
  total: number;
  page: number;
  page_size: number;
  items: TrajectoryItem[];
}

// ── Helpers ──

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

// ── TraceQL Result Transformer ──

function transformTraceQLResult(rows: TraceQLRow[]): TrajectoriesResponse {
  if (!rows || rows.length === 0) {
    return { items: [], total: 0, page: 1, page_size: 50 };
  }

  const items: TrajectoryItem[] = rows.map(row => ({
    id: String(row.trajectory_id ?? row.id ?? ''),
    experiment_id: String(row.experiment_id ?? ''),
    iteration_id: String(row.iteration_id ?? ''),
    iteration_num: (row.iteration_num as number) ?? (row.iteration as number) ?? 0,
    task_id: String(row.task_id ?? ''),
    task_language: String(row.task_language ?? ''),
    scaffold: String(row.scaffold ?? ''),
    tool_schema: String(row.tool_schema ?? ''),
    outcome: (row.verify_code as TrajectoryItem['outcome']) ?? 'error',
    reward: (row.reward as number) ?? 0,
    reward_components: (row.reward_components as Record<string, number>) ?? {},
    passed: Boolean(row.passed),
    total_turns: row.turns ?? 0,
    total_events: (row.total_events as number) ?? 0,
    duration_ms: (row.duration_ms as number) ?? 0,
    total_tokens: (row.total_tokens as number) ?? 0,
    input_tokens: row.input_tokens ?? 0,
    output_tokens: row.output_tokens ?? 0,
    tool_call_count: (row.tool_call_count as number) ?? 0,
    tool_success_rate: (row.tool_success_rate as number) ?? 0,
    repeat_action_rate: (row.repeat_action_rate as number) ?? 0,
    error_turn_count: (row.error_turn_count as number) ?? 0,
    first_error_turn: (row.first_error_turn as number) ?? 0,
    llm_time_ratio: (row.llm_time_ratio as number) ?? 0,
    tokens_per_turn: (row.tokens_per_turn as number) ?? 0,
    otel_trace_id: String(row.otel_trace_id ?? ''),
    annotation_count: (row.annotation_count as number) ?? 0,
    created_at: String(row.created_at ?? new Date().toISOString()),
  }));

  return {
    items,
    total: items.length,
    page: 1,
    page_size: 50,
  };
}

// ── Main component ──

export default function TrajectoryExplorer() {
  const { id: pathId } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const [form] = Form.useForm<FilterFormValues>();
  const filterValues = Form.useWatch([], form);

  // Detect dataset mode
  const isDatasetMode = location.pathname.startsWith('/datasets/');
  const datasetName = isDatasetMode ? pathId : undefined;
  const pathExperimentId = isDatasetMode ? undefined : pathId;

  // URL params — locked values and initial filter seeds
  const lockedExperimentId = pathExperimentId || searchParams.get('experiment') || undefined;
  const lockedTaskId = searchParams.get('task') || undefined;
  const urlIteration = searchParams.get('iteration') || undefined;
  const urlLanguage = searchParams.get('language') || undefined;

  // Derive filter values from Form.
  // When filterValues is undefined (form not yet initialized on first render), fall back to the
  // URL params — which are identical to the form's initialValues — so the query key is stable
  // across the first two renders and we don't fire a redundant request.
  const isFormReady = filterValues !== undefined;
  const outcomeFilter = isFormReady ? filterValues.outcome : [];
  const rewardMin = isFormReady ? filterValues.rewardMin : null;
  const rewardMax = isFormReady ? filterValues.rewardMax : null;
  const turnsMin = isFormReady ? filterValues.turnsMin : null;
  const turnsMax = isFormReady ? filterValues.turnsMax : null;
  const rawTaskId = isFormReady ? filterValues.taskId : (lockedTaskId ?? FILTER_ALL);
  const rawIteration = isFormReady ? filterValues.iteration : (urlIteration ?? FILTER_ALL);
  const rawLanguage = isFormReady ? filterValues.language : (urlLanguage ?? FILTER_ALL);
  const rawExperiment = isFormReady ? filterValues.experiment : (lockedExperimentId ?? FILTER_ALL);
  const taskIdApply = rawTaskId && rawTaskId !== FILTER_ALL ? rawTaskId : undefined;
  const iterationApply =
    rawIteration && rawIteration !== FILTER_ALL ? Number(rawIteration) : undefined;
  const languageApply = rawLanguage && rawLanguage !== FILTER_ALL ? rawLanguage : undefined;
  const experimentApply = rawExperiment && rawExperiment !== FILTER_ALL ? rawExperiment : undefined;

  // Sync locked values into form when URL params change
  useEffect(() => {
    form.setFieldsValue({ taskId: lockedTaskId });
  }, [form, lockedTaskId]);
  useEffect(() => {
    form.setFieldsValue({ experiment: lockedExperimentId ?? FILTER_ALL });
  }, [form, lockedExperimentId]);

  // Drawer state
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);

  // Pagination & sorting
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Handle filter value changes (reset page for server-side filters)
  const handleValuesChange = useCallback((changedValues: Partial<FilterFormValues>) => {
    if (
      'experiment' in changedValues ||
      'outcome' in changedValues ||
      'iteration' in changedValues ||
      'language' in changedValues ||
      'rewardMin' in changedValues ||
      'rewardMax' in changedValues ||
      'taskId' in changedValues
    ) {
      setPage(1);
    }
  }, []);

  // Experiment param for server-side filtering: user selection overrides the URL-locked value.
  // This is unified across both modes — experiment mode locks it via URL, dataset mode via select.
  const serverExperimentId = experimentApply ?? lockedExperimentId;

  const { data, isLoading } = useQuery({
    queryKey: [
      'trajectory-explorer-traceql',
      serverExperimentId,
      datasetName,
      taskIdApply,
      iterationApply,
      languageApply,
      outcomeFilter,
      rewardMin,
      rewardMax,
      page,
      pageSize,
      sortBy,
      sortOrder,
    ],
    queryFn: () =>
      queryTraceQL(
        buildTrajectoryListQuery(serverExperimentId, {
          outcome: outcomeFilter.length > 0 ? outcomeFilter : undefined,
          reward_min: rewardMin !== null ? rewardMin : undefined,
          reward_max: rewardMax !== null ? rewardMax : undefined,
          task_id: taskIdApply,
          iteration: iterationApply,
          language: languageApply,
          dataset_name: datasetName,
        })
      ).then(transformTraceQLResult),
    enabled: isDatasetMode ? !!datasetName : !!lockedExperimentId,
    staleTime: 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: false,
  });

  const items = useMemo(() => data?.items ?? [], [data]);

  // Client-side: turns filter only (experiment is handled server-side in both modes)
  const filteredItems = useMemo(() => {
    let result = items;
    if (turnsMin !== null) result = result.filter(t => t.total_turns >= turnsMin);
    if (turnsMax !== null) result = result.filter(t => t.total_turns <= turnsMax);
    return result;
  }, [items, turnsMin, turnsMax]);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSelectedIndex(null);
  }, [filteredItems]);

  const total = filteredItems.length;

  // Outcome stats — separate aggregate query so counts are not capped by the page size.
  const { data: statsData, isLoading: isStatsLoading } = useQuery({
    queryKey: [
      'trajectory-outcome-stats',
      serverExperimentId,
      datasetName,
      taskIdApply,
      iterationApply,
      languageApply,
      outcomeFilter,
    ],
    queryFn: () =>
      queryTraceQL(
        buildOutcomeStatsQuery(
          serverExperimentId,
          taskIdApply,
          datasetName,
          iterationApply,
          outcomeFilter.length > 0 ? outcomeFilter : undefined,
          languageApply
        )
      ),
    enabled: !!serverExperimentId || !!datasetName,
    staleTime: 0,
    refetchOnMount: 'always',
    refetchOnWindowFocus: false,
  });

  const outcomeSummary = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const row of statsData ?? []) {
      const outcome = String(row['verify_code'] ?? '');
      if (outcome) counts[outcome] = (row.trajectory_count as number) ?? 0;
    }
    return counts;
  }, [statsData]);

  const statsTotal = useMemo(
    () => Object.values(outcomeSummary).reduce((sum, n) => sum + n, 0),
    [outcomeSummary]
  );

  // Experiment options derived from loaded items
  const experimentOptions = useMemo(
    () => [
      { label: 'All', value: FILTER_ALL },
      ...Array.from(new Set(items.map(i => i.experiment_id).filter(Boolean)))
        .sort()
        .map(e => ({ label: e, value: e })),
    ],
    [items]
  );

  // Language options (derived from current result set)
  const languageOptions = useMemo(() => {
    const langs = new Set<string>();
    for (const item of items) {
      if (item.task_language) langs.add(item.task_language);
    }
    return [
      { label: 'All', value: FILTER_ALL },
      ...Array.from(langs)
        .sort()
        .map(l => ({ label: l, value: l })),
    ];
  }, [items]);

  // Iteration options derived from loaded items (same pattern as language)
  const iterationOptions = useMemo(() => {
    const nums = Array.from(new Set(items.map(i => i.iteration_num).filter(n => n > 0))).sort(
      (a, b) => a - b
    );
    return [
      { label: 'All', value: FILTER_ALL },
      ...nums.map(n => ({ label: `#${n}`, value: String(n) })),
    ];
  }, [items]);

  // Table change handler
  const handleTableChange = useCallback(
    (
      pagination: TablePaginationConfig,
      _filters: Record<string, FilterValue | null>,
      sorter: SorterResult<TrajectoryItem> | SorterResult<TrajectoryItem>[]
    ) => {
      setPage(pagination.current ?? 1);
      if (!Array.isArray(sorter) && sorter.field) {
        const fieldMap: Record<string, string> = {
          reward: 'reward',
          total_turns: 'total_turns',
          total_tokens: 'total_tokens',
          duration_ms: 'duration_ms',
          tool_success_rate: 'tool_success_rate',
        };
        const field = fieldMap[sorter.field as string] ?? 'created_at';
        setSortBy(field);
        setSortOrder(sorter.order === 'ascend' ? 'asc' : 'desc');
      }
    },
    []
  );

  const columns: TableProps<TrajectoryItem>['columns'] = useMemo(
    () => [
      {
        title: 'Trajectory ID',
        dataIndex: 'id',
        key: 'id',
        width: '15%',
        render: (v: string) => (
          <span className={clsx('font-mono', styles.monoCell)} title={v}>
            {v}
          </span>
        ),
      },
      {
        title: 'Experiment ID',
        dataIndex: 'experiment_id',
        key: 'experiment_id',
        width: 140,
        render: (v: string) => (
          <span className={clsx('font-mono', styles.monoCell)} title={v}>
            {v.slice(0, 16)}
          </span>
        ),
      },
      {
        title: 'Task ID',
        dataIndex: 'task_id',
        key: 'task_id',
        width: '14%',
        ellipsis: { showTitle: true },
        render: (v: string) => (
          <span className={clsx('font-mono', styles.monoCell)} title={v}>
            {v}
          </span>
        ),
      },
      {
        title: 'Language',
        dataIndex: 'task_language',
        key: 'task_language',
        width: 90,
        render: (v: string) => (v ? <Tag>{v}</Tag> : <span className="text-text-disabled">-</span>),
      },
      {
        title: 'Iteration',
        dataIndex: 'iteration_num',
        key: 'iteration_num',
        width: 90,
        sorter: (a, b) => a.iteration_num - b.iteration_num,
        render: (v: number) => (
          <span className={clsx('font-mono', styles.monoCell)}>{v > 0 ? `#${v}` : '-'}</span>
        ),
      },
      {
        title: 'Outcome',
        dataIndex: 'outcome',
        key: 'outcome',
        width: '8%',
        render: (outcome: string) => <OutcomeBadge outcome={outcome as OutcomeType} />,
      },
      {
        title: 'Reward',
        dataIndex: 'reward',
        key: 'reward',
        width: '7%',
        sorter: true,
        render: (v: number) => {
          if (v === undefined || v === null) return '-';
          return (
            <span
              className={clsx('font-mono', styles.monoCellCompact, {
                [styles.rewardPos]: v > 0,
                [styles.rewardNeg]: v < 0,
                [styles.rewardZero]: v === 0,
              })}
            >
              {v.toFixed(2)}
            </span>
          );
        },
      },
      {
        title: 'Turns',
        dataIndex: 'total_turns',
        key: 'total_turns',
        width: '5%',
        sorter: true,
        render: (v: number) => <span className={clsx('font-mono', styles.monoCell)}>{v}</span>,
      },
      {
        title: 'Tokens',
        dataIndex: 'total_tokens',
        key: 'total_tokens',
        width: '7%',
        sorter: true,
        render: (v: number) => (
          <span className={clsx('font-mono', styles.monoCell)}>{formatTokens(v)}</span>
        ),
      },
      {
        title: 'Duration',
        dataIndex: 'duration_ms',
        key: 'duration_ms',
        width: '6%',
        sorter: true,
        render: (v: number) => (
          <span className={clsx('font-mono', styles.monoCell)}>{formatDuration(v)}</span>
        ),
      },
      {
        title: 'Tool OK%',
        dataIndex: 'tool_success_rate',
        key: 'tool_success_rate',
        width: '5%',
        sorter: true,
        render: (v: number) => {
          if (v === undefined || v === null) return '-';
          return <span className={clsx('font-mono', styles.monoCell)}>{formatPct(v)}</span>;
        },
      },
    ],
    []
  );

  if (!lockedExperimentId && !datasetName) {
    return (
      <div className={styles.errorBanner}>
        Select an experiment or dataset to view trajectories.
      </div>
    );
  }
  return (
    <div className={styles.container}>
      {/* Filter Bar */}
      <Form
        form={form}
        component="div"
        initialValues={{
          experiment: lockedExperimentId ?? FILTER_ALL,
          outcome: [],
          iteration: urlIteration ?? FILTER_ALL,
          language: urlLanguage ?? FILTER_ALL,
          rewardMin: null,
          rewardMax: null,
          turnsMin: null,
          turnsMax: null,
          taskId: lockedTaskId ?? FILTER_ALL,
        }}
        className="!mb-1 !gap-1"
        layout="inline"
        onValuesChange={handleValuesChange}
      >
        <Form.Item name="experiment" label="Experiment">
          <Select
            size="small"
            placeholder="All"
            className="!w-[200px]"
            options={
              lockedExperimentId
                ? [{ label: lockedExperimentId, value: lockedExperimentId }]
                : experimentOptions
            }
            disabled={!!lockedExperimentId}
            showSearch
            optionFilterProp="label"
          />
        </Form.Item>
        <Form.Item name="taskId" label="Task ID">
          <Select
            size="small"
            placeholder="All"
            className="!w-[200px]"
            options={
              lockedTaskId
                ? [{ label: lockedTaskId, value: lockedTaskId }]
                : [
                    { label: 'All', value: FILTER_ALL },
                    ...Array.from(new Set(items.map(i => i.task_id)))
                      .sort()
                      .map(id => ({ label: id, value: id })),
                  ]
            }
            disabled={!!lockedTaskId}
            allowClear={!lockedTaskId}
            showSearch
          />
        </Form.Item>
        <Form.Item name="iteration" label="Iteration">
          <Select
            size="small"
            placeholder="All"
            className="!w-[100px] !min-w-[100px] !max-w-[100px]"
            options={iterationOptions}
          />
        </Form.Item>
        <Form.Item name="language" label="Language">
          <Select
            size="small"
            placeholder="All"
            className="!w-[110px] !min-w-[110px] !max-w-[110px]"
            options={languageOptions}
            allowClear
          />
        </Form.Item>
        <Form.Item name="outcome" label="Outcome">
          <Select
            mode="multiple"
            size="small"
            placeholder="All"
            className="!min-w-[120px]"
            options={[
              { label: 'Success', value: 'success' },
              { label: 'Failure', value: 'failure' },
              { label: 'Timeout', value: 'timeout' },
              { label: 'Error', value: 'error' },
            ]}
            allowClear
          />
        </Form.Item>
        <Form.Item label="Reward">
          <div className={styles.filterRangeCluster}>
            <Form.Item name="rewardMin" noStyle>
              <InputNumber
                size="small"
                placeholder="min"
                step={0.1}
                className="!w-16 !min-w-16 !max-w-16"
              />
            </Form.Item>
            <span className={styles.filterDash}>–</span>
            <Form.Item name="rewardMax" noStyle>
              <InputNumber
                size="small"
                placeholder="max"
                step={0.1}
                className="!w-16 !min-w-16 !max-w-16"
              />
            </Form.Item>
          </div>
        </Form.Item>

        <Form.Item label="Turns">
          <div className={styles.filterRangeCluster}>
            <Form.Item name="turnsMin" noStyle>
              <InputNumber
                size="small"
                placeholder="min"
                min={1}
                className="!w-16 !min-w-16 !max-w-16"
              />
            </Form.Item>
            <span className={styles.filterDash}>–</span>
            <Form.Item name="turnsMax" noStyle>
              <InputNumber
                size="small"
                placeholder="max"
                min={1}
                className="!w-16 !min-w-16 !max-w-16"
              />
            </Form.Item>
          </div>
        </Form.Item>
      </Form>
      <div className={styles.summaryBar}>
        <span>
          <strong className={styles.summaryCount}>{statsTotal.toLocaleString()}</strong>{' '}
          trajectories
        </span>
        {Object.entries(outcomeSummary)
          .filter(([, count]) => count > 0)
          .map(([outcome, count]) => (
            <span key={outcome}>
              <OutcomeBadge outcome={outcome as OutcomeType} />{' '}
              <span className={styles.summaryOutcomeCount}>{count}</span>
            </span>
          ))}
        {(isLoading || isStatsLoading) && <Spin size="small" />}
      </div>

      {/* Trajectories Table */}
      <Table<TrajectoryItem>
        dataSource={filteredItems}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: false,
          showTotal: (t, range) => `${range[0]}-${range[1]} of ${t}`,
          size: 'small',
        }}
        onChange={handleTableChange}
        onRow={(_, rowIndex) => ({
          onClick: () => setSelectedIndex(rowIndex!),
          style: { cursor: 'pointer' },
        })}
        className={styles.trajectoriesTable}
        size="small"
      />

      <Drawer
        open={selectedIndex !== null}
        onClose={() => setSelectedIndex(null)}
        width={1100}
        title={
          selectedIndex !== null
            ? `Trajectory Viewer  ${selectedIndex + 1} / ${filteredItems.length}`
            : 'Trajectory Viewer'
        }
        extra={
          <Space size={4}>
            <Tooltip title="Previous trajectory">
              <Button
                size="small"
                icon={<UpOutlined />}
                disabled={selectedIndex === null || selectedIndex === 0}
                onClick={() => setSelectedIndex(i => (i !== null && i > 0 ? i - 1 : i))}
              />
            </Tooltip>
            <Tooltip title="Next trajectory">
              <Button
                size="small"
                icon={<DownOutlined />}
                disabled={selectedIndex === null || selectedIndex >= filteredItems.length - 1}
                onClick={() =>
                  setSelectedIndex(i => (i !== null && i < filteredItems.length - 1 ? i + 1 : i))
                }
              />
            </Tooltip>
          </Space>
        }
        styles={{ body: { padding: '24px' } }}
      >
        {selectedIndex !== null && filteredItems[selectedIndex] && (
          <TrajectoryViewerPanel
            key={filteredItems[selectedIndex].otel_trace_id || filteredItems[selectedIndex].id}
            id={filteredItems[selectedIndex].otel_trace_id || filteredItems[selectedIndex].id}
          />
        )}
      </Drawer>
    </div>
  );
}
