import { useMemo } from 'react';
import clsx from 'clsx';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Select, Spin, Table, Tag, Form } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import ReactECharts from 'echarts-for-react';
import {
  fetchIterations,
  fetchPassRateDiff,
  fetchCrossAnalysis,
  fetchExtremeCases,
} from '../../api/stats';
import { colors } from '../../styles/theme';
import { formatPct } from '../../utils/format';
import styles from './styles.module.css';
import type {
  PassRateDiffItem,
  CrossAnalysisCellData,
  ExtremeCaseItem,
  IterationItem,
} from '../../types';

// ── Types ──

interface FilterFormValues {
  stepA: number | undefined;
  stepB: number | undefined;
  rowDim: string;
  colDim: string;
  changeFilter: string;
}

export default function PassRateDiff() {
  const { id: experimentId } = useParams<{ id: string }>();
  const [form] = Form.useForm<FilterFormValues>();
  const filterValues = Form.useWatch([], form);

  const stepA = filterValues?.stepA;
  const stepB = filterValues?.stepB;
  const rowDim = filterValues?.rowDim ?? 'scaffold';
  const colDim = filterValues?.colDim ?? 'tool_schema';
  const changeFilterVal = filterValues?.changeFilter ?? 'all';
  const changeFilter = changeFilterVal === 'all' ? undefined : changeFilterVal;

  // Fetch iterations for step selector
  const { data: iterationsData } = useQuery({
    queryKey: ['iterations', experimentId],
    queryFn: () => fetchIterations(experimentId!),
    enabled: !!experimentId,
  });

  const iterations = iterationsData?.items ?? [];
  const stepOptions = iterations.map((it: IterationItem) => ({
    value: it.iteration_num,
    label: `Step ${it.iteration_num}`,
  }));

  // Auto-select first and last steps
  const effectiveStepA = stepA ?? (iterations.length > 1 ? iterations[0].iteration_num : undefined);
  const effectiveStepB =
    stepB ?? (iterations.length > 0 ? iterations[iterations.length - 1].iteration_num : undefined);

  const stepsReady = effectiveStepA !== undefined && effectiveStepB !== undefined;

  // Fetch pass rate diff
  const { data: diffData, isLoading: diffLoading } = useQuery({
    queryKey: ['passRateDiff', experimentId, effectiveStepA, effectiveStepB],
    queryFn: () => fetchPassRateDiff(experimentId!, effectiveStepA!, effectiveStepB!),
    enabled: !!experimentId && stepsReady,
  });

  // Fetch cross analysis
  const { data: crossData } = useQuery({
    queryKey: ['crossAnalysis', experimentId, effectiveStepA, effectiveStepB, rowDim, colDim],
    queryFn: () =>
      fetchCrossAnalysis(experimentId!, effectiveStepA!, effectiveStepB!, rowDim, colDim),
    enabled: !!experimentId && stepsReady,
  });

  // Fetch extreme cases
  const { data: extremeData } = useQuery({
    queryKey: ['extremeCases', experimentId, effectiveStepA, effectiveStepB],
    queryFn: () => fetchExtremeCases(experimentId!, effectiveStepA!, effectiveStepB!, 0.2),
    enabled: !!experimentId && stepsReady,
  });

  // Pie chart for summary
  const pieOption = useMemo(() => {
    if (!diffData) return {};
    const { summary } = diffData;
    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      series: [
        {
          type: 'pie',
          radius: ['40%', '70%'],
          data: [
            { value: summary.improved, name: 'Improved', itemStyle: { color: colors.success } },
            {
              value: summary.unchanged,
              name: 'Unchanged',
              itemStyle: { color: colors.textTertiary },
            },
            { value: summary.degraded, name: 'Degraded', itemStyle: { color: colors.error } },
          ],
          label: {
            color: colors.textSecondary,
            formatter: '{b}: {c} ({d}%)',
          },
        },
      ],
    };
  }, [diffData]);

  // Filtered items
  const filteredItems = useMemo(() => {
    if (!diffData) return [];
    if (!changeFilter) return diffData.items;
    return diffData.items.filter(item => item.change_group === changeFilter);
  }, [diffData, changeFilter]);

  // Detail table columns
  const detailColumns: ColumnsType<PassRateDiffItem> = [
    {
      title: 'Task ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 140,
      render: (v: string) => <span className={clsx('font-mono', 'text-sm')}>{v}</span>,
    },
    { title: 'Language', dataIndex: 'language', key: 'language', width: 100 },
    { title: 'Category', dataIndex: 'category', key: 'category', width: 120 },
    {
      title: 'Pass Rate A',
      dataIndex: 'pass_rate_a',
      key: 'pass_rate_a',
      width: 110,
      sorter: (a, b) => a.pass_rate_a - b.pass_rate_a,
      render: (v: number) => formatPct(v),
    },
    {
      title: 'Pass Rate B',
      dataIndex: 'pass_rate_b',
      key: 'pass_rate_b',
      width: 110,
      sorter: (a, b) => a.pass_rate_b - b.pass_rate_b,
      render: (v: number) => formatPct(v),
    },
    {
      title: 'Change',
      dataIndex: 'change',
      key: 'change',
      width: 100,
      defaultSortOrder: 'descend',
      sorter: (a, b) => Math.abs(a.change) - Math.abs(b.change),
      render: (v: number) => (
        <span
          className={clsx('font-semibold', {
            'tone-success': v > 0,
            'tone-error': v < 0,
            'text-tertiary': v === 0,
          })}
        >
          {v > 0 ? '+' : ''}
          {formatPct(v)}
        </span>
      ),
    },
    {
      title: 'Group',
      dataIndex: 'change_group',
      key: 'change_group',
      width: 100,
      render: (v: string) => (
        <Tag color={v === 'improved' ? 'green' : v === 'degraded' ? 'red' : 'default'}>{v}</Tag>
      ),
    },
  ];

  // Cross analysis table
  const crossColumns = useMemo(() => {
    if (!crossData) return [];
    const cols: ColumnsType<Record<string, unknown>> = [
      {
        title: crossData.row_dimension,
        dataIndex: 'rowKey',
        key: 'rowKey',
        width: 120,
        fixed: 'left',
      },
    ];
    for (const col of crossData.cols) {
      cols.push({
        title: col,
        dataIndex: col,
        key: col,
        width: 180,
        render: (cell: CrossAnalysisCellData) =>
          cell ? (
            <div className="font-size-sm">
              <span className="tone-success">↑{cell.improved}</span>
              {' / '}
              <span className="text-tertiary">={cell.unchanged}</span>
              {' / '}
              <span className="tone-error">↓{cell.degraded}</span>
            </div>
          ) : (
            '-'
          ),
      });
    }
    return cols;
  }, [crossData]);

  const crossDataSource = useMemo(() => {
    if (!crossData) return [];
    return crossData.rows.map(row => {
      const record: Record<string, unknown> = { key: row, rowKey: row };
      for (const col of crossData.cols) {
        record[col] = crossData.cells[row]?.[col];
      }
      return record;
    });
  }, [crossData]);

  // Extreme case columns
  const extremeColumns: ColumnsType<ExtremeCaseItem> = [
    { title: 'Task ID', dataIndex: 'task_id', key: 'task_id', width: 140 },
    { title: 'Language', dataIndex: 'language', key: 'language', width: 100 },
    {
      title: 'Rate A',
      dataIndex: 'pass_rate_a',
      key: 'pass_rate_a',
      width: 100,
      render: (v: number) => formatPct(v),
    },
    {
      title: 'Rate B',
      dataIndex: 'pass_rate_b',
      key: 'pass_rate_b',
      width: 100,
      render: (v: number) => formatPct(v),
    },
    {
      title: 'Change',
      dataIndex: 'change',
      key: 'change',
      width: 100,
      render: (v: number) => (
        <span
          className={clsx('font-semibold', {
            'tone-success': v > 0,
            'tone-error': v <= 0,
          })}
        >
          {v > 0 ? '+' : ''}
          {formatPct(v)}
        </span>
      ),
    },
  ];

  if (!experimentId) return null;

  return (
    <Form
      form={form}
      component={false}
      initialValues={{
        stepA: undefined,
        stepB: undefined,
        rowDim: 'scaffold',
        colDim: 'tool_schema',
        changeFilter: 'all',
      }}
    >
      <div className={styles.container}>
        <h1 className={styles.pageTitle}>Pass Rate Diff Analysis</h1>

        <div className={styles.filterRow}>
          <div className={styles.filterGroup}>
            <span className={styles.filterLabel}>Step A:</span>
            <Form.Item name="stepA" noStyle>
              <Select options={stepOptions} className={styles.w140} size="small" />
            </Form.Item>
          </div>
          <div className={styles.filterGroup}>
            <span className={styles.filterLabel}>Step B:</span>
            <Form.Item name="stepB" noStyle>
              <Select options={stepOptions} className={styles.w140} size="small" />
            </Form.Item>
          </div>
          <div className={styles.filterGroup}>
            <span className={styles.filterLabel}>Row:</span>
            <Form.Item name="rowDim" noStyle>
              <Select
                className={styles.w150}
                size="small"
                options={[
                  { value: 'scaffold', label: 'Scaffold' },
                  { value: 'tool_schema', label: 'Tool Schema' },
                  { value: 'language', label: 'Language' },
                ]}
              />
            </Form.Item>
          </div>
          <div className={styles.filterGroup}>
            <span className={styles.filterLabel}>Col:</span>
            <Form.Item name="colDim" noStyle>
              <Select
                className={styles.w150}
                size="small"
                options={[
                  { value: 'tool_schema', label: 'Tool Schema' },
                  { value: 'language', label: 'Language' },
                ]}
              />
            </Form.Item>
          </div>
        </div>

        {diffLoading && (
          <div className={styles.loadingWrap}>
            <Spin size="large" />
          </div>
        )}

        {diffData && (
          <>
            {/* Summary + Pie */}
            <div className={styles.chartsGrid}>
              <div className={styles.cardPanel}>
                <div className={styles.sectionTitle}>Change Distribution</div>
                <ReactECharts option={pieOption} style={{ height: 280 }} />
              </div>

              <div className={styles.cardPanel}>
                <div className={styles.sectionTitle}>
                  {crossData?.row_dimension ?? 'Row'} × {crossData?.col_dimension ?? 'Col'}
                </div>
                {crossData ? (
                  <Table
                    columns={crossColumns}
                    dataSource={crossDataSource}
                    size="small"
                    pagination={false}
                    scroll={{ x: 'max-content' }}
                  />
                ) : (
                  <div className={styles.chartPlaceholder}>Loading...</div>
                )}
              </div>
            </div>

            <div className={styles.cardPanelMb}>
              <div className={styles.toolbarRow}>
                <span className={styles.toolbarTitle}>
                  Change Details ({filteredItems.length} tasks)
                </span>
                <Form.Item name="changeFilter" noStyle>
                  <Select
                    size="small"
                    className={styles.w130}
                    options={[
                      { value: 'all', label: 'All' },
                      { value: 'improved', label: '↑ Improved' },
                      { value: 'unchanged', label: '= Unchanged' },
                      { value: 'degraded', label: '↓ Degraded' },
                    ]}
                  />
                </Form.Item>
              </div>
              <Table<PassRateDiffItem>
                columns={detailColumns}
                dataSource={filteredItems}
                rowKey="task_id"
                size="small"
                pagination={{ pageSize: 20 }}
              />
            </div>

            {/* Extreme Cases (TASK-035) */}
            {extremeData && extremeData.total_extreme > 0 && (
              <div className={styles.cardPanel}>
                <div className={styles.sectionTitle}>
                  Extreme Cases (|change| &gt; {extremeData.threshold * 100}%)
                </div>
                <div className={styles.extremeGrid}>
                  <div>
                    <div className={styles.extremeColTitleImproved}>
                      Top Improved ({extremeData.extreme_improved.length})
                    </div>
                    <Table<ExtremeCaseItem>
                      columns={extremeColumns}
                      dataSource={extremeData.extreme_improved.slice(0, 10)}
                      rowKey="task_id"
                      size="small"
                      pagination={false}
                    />
                  </div>
                  <div>
                    <div className={styles.extremeColTitleDegraded}>
                      Top Degraded ({extremeData.extreme_degraded.length})
                    </div>
                    <Table<ExtremeCaseItem>
                      columns={extremeColumns}
                      dataSource={extremeData.extreme_degraded.slice(0, 10)}
                      rowKey="task_id"
                      size="small"
                      pagination={false}
                    />
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </Form>
  );
}
