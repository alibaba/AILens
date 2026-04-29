import { useMemo, useState, useCallback, useEffect, forwardRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';
import { Table, Select, Tooltip, Form } from 'antd';
import type { TableProps, TablePaginationConfig } from 'antd';
import type { FilterValue, SorterResult } from 'antd/es/table/interface';
import { useNavigate, useSearchParams } from 'react-router-dom';
import ReactECharts from 'echarts-for-react';
import OutcomeBadge from '../../components/shared/OutcomeBadge';
import { queryTraceQL } from '../../api/traceql';
import type { TraceQLRow } from '../../api/traceql';
import { buildTaskSummaryQuery } from '../../queries/task';
import type { TaskLibraryItem } from '../../types';
import { colors, fontSize } from '../../styles/theme';
import { formatPct } from '../../utils/format';
import { Tag } from 'antd';
import styles from './styles.module.css';

type DifficultyLevel = 'trivial' | 'easy' | 'medium' | 'hard' | 'impossible';

/** Sentinel for Select "All"; never stored in URL or sent to TraceQL. */
const FILTER_ALL = '__all__' as const;

interface FilterFormValues {
  outcome: string[];
  language: string | undefined;
  taskId: string | undefined;
  difficultyFilter?: DifficultyLevel[];
}

function classifyDifficulty(passRate: number): DifficultyLevel {
  if (passRate >= 0.7) return 'trivial';
  if (passRate >= 0.3) return 'easy';
  if (passRate >= 0.1) return 'medium';
  if (passRate > 0) return 'hard';
  return 'impossible';
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function getDifficultyLabel(passRate: number): { label: string; color: string } | null {
  if (passRate >= 0.7) return { label: 'Trivial [70%~100%]', color: '#22C55E' };
  if (passRate >= 0.3) return { label: 'Easy [30%~70%)', color: '#4ADE80' };
  if (passRate >= 0.1) return { label: 'Medium [10%~30%)', color: '#F59E0B' };
  if (passRate > 0) return { label: 'Hard (0%~10%)', color: '#F97316' };
  return { label: 'Impossible [0%]', color: '#EF4444' };
}

const TableBodyCell = forwardRef<
  HTMLTableCellElement,
  React.TdHTMLAttributes<HTMLTableCellElement>
>(({ className, ...rest }, ref) => (
  <td ref={ref} {...rest} className={clsx(styles.dataCell, className)} />
));
TableBodyCell.displayName = 'TableBodyCell';

const taskTableComponents: TableProps<TaskLibraryItem>['components'] = {
  body: { cell: TableBodyCell },
};

// ── Main component ──

export default function TaskLibrary() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [form] = Form.useForm<FilterFormValues>();

  // Filters driven by URL search params
  const outcomeFilter = useMemo(() => {
    const p = searchParams.get('outcome');
    return p ? p.split(',') : [];
  }, [searchParams]);
  const languageFilter = useMemo(() => {
    const raw = searchParams.get('language') ?? undefined;
    if (raw === undefined || raw === '' || raw === FILTER_ALL) return undefined;
    return raw;
  }, [searchParams]);
  const taskIdFilter = useMemo(() => {
    const raw = searchParams.get('taskId') ?? undefined;
    if (raw === undefined || raw === '' || raw === FILTER_ALL) return undefined;
    return raw;
  }, [searchParams]);
  const difficultyFilter = useMemo(() => {
    const p = searchParams.get('difficulty');
    return p ? (p.split(',') as DifficultyLevel[]) : [];
  }, [searchParams]);

  // Sync form from URL search params
  useEffect(() => {
    form.setFieldsValue({
      outcome: outcomeFilter,
      language: languageFilter ?? FILTER_ALL,
      taskId: taskIdFilter ?? FILTER_ALL,
      difficultyFilter: difficultyFilter.length > 0 ? difficultyFilter : undefined,
    });
  }, [form, outcomeFilter, languageFilter, taskIdFilter, difficultyFilter]);

  // Chart collapse state — default collapsed
  const [chartCollapsed, setChartCollapsed] = useState(() => {
    const saved = localStorage.getItem('task-chart-collapsed');
    return saved === 'false' ? false : true;
  });
  const [showCollapseHint, setShowCollapseHint] = useState(() => {
    return localStorage.getItem('task-chart-collapse-hint') !== '1';
  });

  // Persist collapse state
  useEffect(() => {
    localStorage.setItem('task-chart-collapsed', String(chartCollapsed));
  }, [chartCollapsed]);

  const setFilter = useCallback(
    (updates: {
      outcome?: string[];
      language?: string;
      taskId?: string;
      difficulty?: DifficultyLevel[];
    }) => {
      const params = new URLSearchParams(searchParams);
      if (updates.outcome?.length) params.set('outcome', updates.outcome.join(','));
      else params.delete('outcome');
      if (updates.language && updates.language !== FILTER_ALL) {
        params.set('language', updates.language);
      } else {
        params.delete('language');
      }
      if (updates.taskId && updates.taskId !== FILTER_ALL) {
        params.set('taskId', updates.taskId);
      } else {
        params.delete('taskId');
      }
      if (updates.difficulty?.length) params.set('difficulty', updates.difficulty.join(','));
      else params.delete('difficulty');
      setSearchParams(params, { replace: true });
    },
    [searchParams, setSearchParams]
  );
  // Pagination & sorting (applied per-view)
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [sortBy, setSortBy] = useState<string>('rollout_count');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const handleValuesChange = useCallback(
    (_changedValues: Partial<FilterFormValues>, allValues: FilterFormValues) => {
      setFilter({
        outcome: allValues.outcome,
        language: allValues.language,
        taskId: allValues.taskId,
        difficulty: allValues.difficultyFilter,
      });
      setPage(1);
    },
    [setFilter]
  );

  // Language (and taskId) are applied client-side so the dataset always exposes
  // all languages / task ids for dropdowns while one language is selected.
  const query = useMemo(
    () =>
      buildTaskSummaryQuery({
        outcome: outcomeFilter.length > 0 ? outcomeFilter : undefined,
      }),
    [outcomeFilter]
  );

  const { data: taskItems = [], isLoading } = useQuery({
    queryKey: ['task-summary', query],
    queryFn: () => queryTraceQL(query).then(rows => rows.map(toTaskSummaryItem)),
    staleTime: 60_000,
  });

  // Client-side filtering for taskId and difficulty
  const filteredItems = useMemo(() => {
    let result = taskItems;
    if (languageFilter && languageFilter !== FILTER_ALL) {
      result = result.filter(t => t.task_language === languageFilter);
    }
    if (taskIdFilter && taskIdFilter !== FILTER_ALL) {
      const q = taskIdFilter.toLowerCase();
      result = result.filter(t => t.task_id.toLowerCase().includes(q));
    }
    if (difficultyFilter.length > 0) {
      result = result.filter(t => difficultyFilter.includes(classifyDifficulty(t.pass_rate)));
    }
    return result;
  }, [taskItems, languageFilter, taskIdFilter, difficultyFilter]);

  // Client-side sorting & pagination
  const sortedAndPaginatedItems = useMemo(() => {
    const fieldMap: Record<string, (item: TaskLibraryItem) => number> = {
      experiment_count: item => item.experiment_count,
      trajectory_count: item => item.trajectory_count,
      pass_rate: item => item.pass_rate,
      max_turns: item => item.max_turns,
      min_turns: item => item.min_turns,
      max_duration_ms: item => item.max_duration_ms,
      min_duration_ms: item => item.min_duration_ms,
      avg_turns: item => item.avg_turns,
      avg_duration_ms: item => item.avg_duration_ms,
    };
    const getter = fieldMap[sortBy];
    if (!getter) return filteredItems;
    const sorted = [...filteredItems].sort((a, b) => {
      const diff = getter(a) - getter(b);
      return sortOrder === 'desc' ? -diff : diff;
    });
    const start = (page - 1) * pageSize;
    return sorted.slice(start, start + pageSize);
  }, [filteredItems, sortBy, sortOrder, page, pageSize]);

  const total = filteredItems.length;

  // Languages from data
  const languages = useMemo(() => {
    const s = new Set<string>();
    for (const item of taskItems) {
      if (item.task_language) s.add(item.task_language);
    }
    return Array.from(s).sort();
  }, [taskItems]);

  // Difficulty analysis: Language × Difficulty cross-tab
  type DifficultyCounts = Record<DifficultyLevel, number>;
  interface DifficultyAnalysisRow {
    language: string;
    counts: DifficultyCounts;
    total: number;
  }
  const difficultyAnalysisRows = useMemo((): DifficultyAnalysisRow[] => {
    const map = new Map<string, DifficultyCounts>();
    for (const item of taskItems) {
      const lang = item.task_language || 'Unknown';
      if (!map.has(lang)) {
        map.set(lang, { trivial: 0, easy: 0, medium: 0, hard: 0, impossible: 0 });
      }
      const counts = map.get(lang)!;
      const d = classifyDifficulty(item.pass_rate);
      counts[d] += 1;
    }
    const rows: DifficultyAnalysisRow[] = [];
    for (const [lang, counts] of map) {
      const total = Object.values(counts).reduce((s, n) => s + n, 0);
      rows.push({ language: lang === 'Unknown' ? '-' : lang, counts, total });
    }
    return rows.sort((a, b) => {
      const aIsUnknown = a.language === '-';
      const bIsUnknown = b.language === '-';
      if (aIsUnknown && !bIsUnknown) return 1;
      if (!aIsUnknown && bIsUnknown) return -1;
      return b.total - a.total;
    });
  }, [taskItems]);

  const difficultyAnalysisTotals = useMemo(() => {
    const totals: DifficultyCounts = { trivial: 0, easy: 0, medium: 0, hard: 0, impossible: 0 };
    for (const row of difficultyAnalysisRows) {
      for (const d of ['trivial', 'easy', 'medium', 'hard', 'impossible'] as DifficultyLevel[]) {
        totals[d] += row.counts[d];
      }
    }
    return { ...totals, total: Object.values(totals).reduce((s, n) => s + n, 0) };
  }, [difficultyAnalysisRows]);

  // Task classification for pie chart
  const taskClassification = useMemo(() => {
    const counts = { all_pass: 0, all_fail: 0, mixed: 0, unverified: 0 };
    for (const item of taskItems) {
      const hasPass = item.pass_count > 0;
      const hasFail = item.fail_count > 0;
      if (hasPass && hasFail) counts.mixed++;
      else if (hasPass) counts.all_pass++;
      else if (hasFail) counts.all_fail++;
      else counts.unverified++;
    }
    return counts;
  }, [taskItems]);

  // Table change handler
  const handleTableChange = useCallback(
    (
      pagination: TablePaginationConfig,
      _filters: Record<string, FilterValue | null>,
      sorter: SorterResult<TaskLibraryItem> | SorterResult<TaskLibraryItem>[]
    ) => {
      setPage(pagination.current ?? 1);
      if (!Array.isArray(sorter) && sorter.field) {
        const fieldMap: Record<string, string> = {
          experiment_count: 'experiment_count',
          trajectory_count: 'trajectory_count',
          pass_rate: 'pass_rate',
          max_turns: 'max_turns',
          min_turns: 'min_turns',
          max_duration_ms: 'max_duration_ms',
          min_duration_ms: 'min_duration_ms',
          avg_turns: 'avg_turns',
          avg_duration_ms: 'avg_duration_ms',
        };
        const field = fieldMap[sorter.field as string] ?? 'pass_rate';
        setSortBy(field);
        setSortOrder(sorter.order === 'ascend' ? 'asc' : 'desc');
      }
    },
    []
  );

  // Columns for first-level (task summary)
  const columns: TableProps<TaskLibraryItem>['columns'] = useMemo(
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
        title: 'Experiments',
        dataIndex: 'experiment_count',
        key: 'experiment_count',
        width: 100,
        sorter: true,
        render: (v: number) => <span>{v}</span>,
      },
      {
        title: 'Trajectories',
        dataIndex: 'trajectory_count',
        key: 'trajectory_count',
        width: 110,
        sorter: true,
        render: (v: number) => <span className="font-medium text-text-primary">{v}</span>,
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
        render: (_: unknown, record: TaskLibraryItem) => (
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
        render: (v: number) => <span>{v}</span>,
      },
      {
        title: 'Min Turns',
        dataIndex: 'min_turns',
        key: 'min_turns',
        width: 90,
        sorter: true,
        render: (v: number) => <span>{v}</span>,
      },
      {
        title: 'Max Duration',
        dataIndex: 'max_duration_ms',
        key: 'max_duration_ms',
        width: 110,
        sorter: true,
        render: (v: number) => formatDuration(v),
      },
      {
        title: 'Min Duration',
        dataIndex: 'min_duration_ms',
        key: 'min_duration_ms',
        width: 110,
        sorter: true,
        render: (v: number) => formatDuration(v),
      },
      {
        title: 'Avg Turns',
        dataIndex: 'avg_turns',
        key: 'avg_turns',
        width: 90,
        sorter: true,
        render: (v: number) => v.toFixed(1),
      },
      {
        title: 'Avg Duration',
        dataIndex: 'avg_duration_ms',
        key: 'avg_duration_ms',
        width: 110,
        sorter: true,
        render: (v: number) => formatDuration(v),
      },
      {
        title: 'Difficulty',
        key: 'difficulty',
        width: 150,
        sorter: (a, b) => a.pass_rate - b.pass_rate,
        render: (_: unknown, record: TaskLibraryItem) => {
          const difficulty = getDifficultyLabel(record.pass_rate);
          if (!difficulty) return '-';
          return <Tag color={difficulty.color}>{difficulty.label}</Tag>;
        },
      },
    ],
    []
  );

  return (
    <div className={styles.page}>
      <h1 className={styles.pageTitle}>Task Dashboard</h1>

      <p className={styles.lede}>
        A Task — also named as a "Problem" or "Instance" in some RL contexts — represents a solvable
        problem. It can be placed across multiple Experiments and solved repeatedly, producing
        multiple Trajectories.
      </p>

      <Form form={form} component={false} onValuesChange={handleValuesChange}>
        <div className={styles.filterBar}>
          <div className={styles.filterField}>
            <span className={styles.filterLabel}>Task ID:</span>
            <Form.Item name="taskId" noStyle>
              <Select
                size="small"
                placeholder="All"
                className={styles.w160}
                options={[
                  { label: 'All', value: FILTER_ALL },
                  ...Array.from(new Set(taskItems.map(i => i.task_id))).map(id => ({
                    label: id,
                    value: id,
                  })),
                ]}
                allowClear
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
              />
            </Form.Item>
          </div>
          <div className={styles.filterField}>
            <span className={styles.filterLabel}>Language:</span>
            <Form.Item name="language" noStyle>
              <Select
                size="small"
                placeholder="All"
                className={styles.w120}
                options={[
                  { label: 'All', value: FILTER_ALL },
                  ...languages.map(lang => ({ label: lang, value: lang })),
                ]}
                allowClear
              />
            </Form.Item>
          </div>
          <div className={styles.filterField}>
            <span className={styles.filterLabel}>Outcome:</span>
            <Form.Item name="outcome" noStyle>
              <Select
                mode="multiple"
                size="small"
                placeholder="All"
                className={styles.minW120}
                options={[
                  { label: 'Success', value: 'success' },
                  { label: 'Failure', value: 'failure' },
                  { label: 'Timeout', value: 'timeout' },
                  { label: 'Error', value: 'error' },
                ]}
                allowClear
              />
            </Form.Item>
            <Form.Item name="difficultyFilter" noStyle>
              <Select
                mode="multiple"
                size="small"
                placeholder="All"
                style={{ minWidth: 200 }}
                options={[
                  { label: 'Trivial [70%~100%]', value: 'trivial' },
                  { label: 'Easy [30%~70%)', value: 'easy' },
                  { label: 'Medium [10%~30%)', value: 'medium' },
                  { label: 'Hard (0%~10%)', value: 'hard' },
                  { label: 'Impossible [0%]', value: 'impossible' },
                ]}
                allowClear
              />
            </Form.Item>
          </div>
        </div>
      </Form>
      <Tooltip
        placement="topRight"
        title="Click here to collapse/expand chart area"
        open={showCollapseHint}
      >
        <div className={styles.chartCard}>
          <div
            className={clsx(styles.chartHeader, {
              [styles.chartHeaderDivider]: !chartCollapsed,
            })}
            onClick={() => {
              setChartCollapsed(v => !v);
              if (showCollapseHint) {
                setShowCollapseHint(false);
                localStorage.setItem('task-chart-collapse-hint', '1');
              }
            }}
          >
            <span className={styles.chartTitle}>Task Outcome Statistics</span>
            <div className={styles.chartHeaderRight}>
              <span className={styles.chartStats}>
                All Correct: <span className={styles.statPass}>{taskClassification.all_pass}</span>
                {' · '}
                All Wrong: <span className={styles.statFail}>{taskClassification.all_fail}</span>
                {' · '}
                Mixed: <span className={styles.statMixed}>{taskClassification.mixed}</span>
                {' · '}
                Unverified:{' '}
                <span className={styles.statUnverified}>{taskClassification.unverified}</span>
              </span>
              <span className={styles.collapseBadge}>
                <span
                  className={clsx(styles.chevron, {
                    [styles.chevronExpanded]: !chartCollapsed,
                  })}
                >
                  ▼
                </span>
              </span>
            </div>
          </div>
          {!chartCollapsed && (
            <div className={styles.chartBody}>
              {/* Left: Pie Chart */}
              <div className={styles.chartHalf}>
                <ReactECharts
                  option={{
                    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
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
                        },
                        emphasis: {
                          label: {
                            show: true,
                            fontSize: fontSize.sm,
                            fontWeight: 'bold',
                            color: colors.textPrimary,
                          },
                        },
                        labelLayout: {
                          hideOverlap: true,
                        },
                        data: [
                          {
                            name: 'All Correct',
                            value: taskClassification.all_pass,
                            itemStyle: { color: '#52c41a' },
                          },
                          {
                            name: 'All Wrong',
                            value: taskClassification.all_fail,
                            itemStyle: { color: '#ff4d4f' },
                          },
                          {
                            name: 'Mixed',
                            value: taskClassification.mixed,
                            itemStyle: { color: '#faad14' },
                          },
                          {
                            name: 'Unverified',
                            value: taskClassification.unverified,
                            itemStyle: { color: '#666' },
                          },
                        ].filter(d => d.value > 0),
                      },
                    ],
                  }}
                  style={{ height: 250 }}
                  opts={{ renderer: 'svg' }}
                />
              </div>

              {/* Right: Bar Chart */}
              <div className={styles.chartHalf}>
                <ReactECharts
                  option={{
                    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                    grid: { left: 60, right: 20, top: 20, bottom: 30 },
                    xAxis: {
                      type: 'value',
                      axisLabel: { color: colors.textSecondary },
                      splitLine: { lineStyle: { color: colors.borderSecondary } },
                    },
                    yAxis: {
                      type: 'category',
                      data: ['All Correct', 'All Wrong', 'Mixed', 'Unverified'],
                      axisLabel: { color: colors.textSecondary },
                      axisLine: { lineStyle: { color: colors.borderSecondary } },
                    },
                    series: [
                      {
                        type: 'bar',
                        data: [
                          { value: taskClassification.all_pass, itemStyle: { color: '#52c41a' } },
                          { value: taskClassification.all_fail, itemStyle: { color: '#ff4d4f' } },
                          { value: taskClassification.mixed, itemStyle: { color: '#faad14' } },
                          { value: taskClassification.unverified, itemStyle: { color: '#666' } },
                        ],
                        barWidth: 24,
                        label: {
                          show: true,
                          position: 'right',
                          color: colors.textSecondary,
                        },
                      },
                    ],
                  }}
                  style={{ height: 250 }}
                  opts={{ renderer: 'svg' }}
                />
              </div>
            </div>
          )}
        </div>
      </Tooltip>

      {/* Tasks Table */}
      <Table<TaskLibraryItem>
        className={styles.tableShell}
        bordered
        components={taskTableComponents}
        dataSource={sortedAndPaginatedItems}
        columns={columns}
        rowKey="task_id"
        loading={isLoading}
        scroll={{ x: 1250 }}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: false,
          showTotal: (t, range) => `${range[0]}-${range[1]} of ${t}`,
          size: 'small',
        }}
        onChange={handleTableChange}
        onRow={record => ({
          onClick: () => {
            const detailParams = new URLSearchParams();
            if (outcomeFilter.length) detailParams.set('outcome', outcomeFilter.join(','));
            if (languageFilter) detailParams.set('language', languageFilter);
            navigate(`/tasks/${encodeURIComponent(record.task_id)}?${detailParams.toString()}`);
          },
          className: styles.clickableRow,
        })}
        size="small"
      />

      {/* Difficulty Analysis Table */}
      <div
        style={{
          marginTop: 24,
          backgroundColor: colors.panelBg,
          border: `1px solid ${colors.borderSecondary}`,
          borderRadius: 8,
          padding: 16,
        }}
      >
        <div
          style={{
            marginBottom: 12,
            fontSize: fontSize.bodyCompact,
            color: colors.textSecondary,
            fontWeight: 600,
          }}
        >
          Difficulty Analysis
        </div>
        <Table<DifficultyAnalysisRow>
          dataSource={[
            ...difficultyAnalysisRows,
            {
              language: 'Total',
              counts: {
                trivial: difficultyAnalysisTotals.trivial,
                easy: difficultyAnalysisTotals.easy,
                medium: difficultyAnalysisTotals.medium,
                hard: difficultyAnalysisTotals.hard,
                impossible: difficultyAnalysisTotals.impossible,
              },
              total: difficultyAnalysisTotals.total,
            } as DifficultyAnalysisRow,
          ]}
          rowKey="language"
          size="small"
          pagination={false}
          rowClassName={record => (record.language === 'Total' ? 'summary-row' : '')}
          columns={[
            {
              title: 'Language',
              dataIndex: 'language',
              key: 'language',
              width: 140,
              render: (v: string) => (
                <span style={{ fontWeight: v === 'Total' ? 700 : 400 }}>{v}</span>
              ),
            },
            ...(['trivial', 'easy', 'medium', 'hard', 'impossible'] as DifficultyLevel[]).map(
              (level, idx) => {
                const diff = getDifficultyLabel(
                  idx === 0 ? 0.75 : idx === 1 ? 0.5 : idx === 2 ? 0.2 : idx === 3 ? 0.05 : 0
                );
                return {
                  title: diff?.label ?? level,
                  key: level,
                  width: 120,
                  render: (_: unknown, record: DifficultyAnalysisRow) => (
                    <span
                      className="font-mono"
                      style={{
                        fontWeight: record.language === 'Total' ? 700 : 400,
                        color:
                          record.language === 'Total' ? colors.textPrimary : colors.textSecondary,
                      }}
                    >
                      {record.counts[level]?.toLocaleString() ?? '-'}
                    </span>
                  ),
                };
              }
            ),
            {
              title: 'Total',
              key: 'total',
              width: 90,
              render: (_: unknown, record: DifficultyAnalysisRow) => (
                <span
                  className="font-mono"
                  style={{
                    fontWeight: record.language === 'Total' ? 700 : 400,
                    color: record.language === 'Total' ? colors.textPrimary : colors.textSecondary,
                  }}
                >
                  {record.total.toLocaleString()}
                </span>
              ),
            },
          ]}
        />
      </div>
    </div>
  );
}

function toTaskSummaryItem(row: TraceQLRow): TaskLibraryItem {
  return {
    task_id: String(row.task_id ?? ''),
    task_language: String(row.task_language ?? ''),
    experiment_count: Number(row.experiment_count ?? 0),
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
