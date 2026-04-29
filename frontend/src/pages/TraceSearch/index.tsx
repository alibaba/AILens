import { useState, useMemo, useCallback } from 'react';
import clsx from 'clsx';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Select, Input, Button, Table, Tooltip, DatePicker, Form } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts/core';
import { BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import dayjs from 'dayjs';
import { useTraceSearch, type TraceSearchResult } from '../../api/traces';
import OutcomeBadge from '../../components/shared/OutcomeBadge';
import ChartPanel from '../../components/shared/ChartPanel';
import { colors, fontSize } from '../../styles/theme';
import { mergeChartOption } from '../../styles/echarts-dark';
import styles from './styles.module.css';

echarts.use([BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer]);

// ── Types ──

interface FilterFormValues {
  serviceName: string;
  status: string;
  timeRange: [dayjs.Dayjs | null, dayjs.Dayjs | null];
  traceIdInput: string;
}

// ── Helpers ──

function percentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  const idx = (p / 100) * (sorted.length - 1);
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return sorted[lo];
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo);
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function buildDurationHistogram(items: TraceSearchResult[]) {
  if (items.length === 0) return { bins: [] as string[], counts: [] as number[] };
  const durations = items.map(t => t.duration_ms);
  const max = Math.max(...durations);
  const binCount = Math.min(12, Math.max(4, Math.ceil(items.length / 5)));
  const binSize = Math.ceil(max / binCount / 100) * 100 || 500;
  const bins: string[] = [];
  const counts: number[] = [];
  for (let i = 0; i < binCount; i++) {
    const lo = i * binSize;
    const hi = lo + binSize;
    bins.push(lo >= 1000 ? `${(lo / 1000).toFixed(1)}s` : `${lo}ms`);
    counts.push(durations.filter(d => d >= lo && d < hi).length);
  }
  return { bins, counts };
}

// ── Component ──

export default function TraceSearch() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Default time range: last 24 hours
  const now = dayjs();
  const defaultStart = now.subtract(24, 'hour');

  const [form] = Form.useForm<FilterFormValues>();

  // Watch individual fields for reactive query
  const serviceName = Form.useWatch('serviceName', form) ?? '';
  const statusVal = Form.useWatch('status', form) ?? '';
  const timeRange = Form.useWatch('timeRange', form);

  const [page, setPage] = useState(1);
  const pageSize = 50;

  // Build query params from watched form values
  const queryParams = useMemo(() => {
    const [startTime, endTime] = timeRange || [null, null];
    if (!startTime || !endTime) return null;
    return {
      start_time: startTime.valueOf(),
      end_time: endTime.valueOf(),
      service_name: serviceName || undefined,
      status: statusVal || undefined,
      limit: 100,
    };
  }, [timeRange, serviceName, statusVal]);

  const { data, isLoading } = useTraceSearch(queryParams ?? { start_time: 0, end_time: 0 });

  // Client-side pagination (since backend doesn't support it)
  const paginatedData = useMemo(() => {
    const allItems = data ?? [];
    const start = (page - 1) * pageSize;
    return allItems.slice(start, start + pageSize);
  }, [data, page, pageSize]);

  // Aggregated stats
  const stats = useMemo(() => {
    const items = data ?? [];
    if (items.length === 0) return { total: 0, errorPct: 0, p50: 0, p99: 0 };
    const sorted = items.map(t => t.duration_ms).sort((a, b) => a - b);
    const errors = items.filter(t => t.status === 'error').length;
    return {
      total: items.length,
      errorPct: (errors / items.length) * 100,
      p50: percentile(sorted, 50),
      p99: percentile(sorted, 99),
    };
  }, [data]);

  // Duration histogram
  const histogram = useMemo(() => buildDurationHistogram(data ?? []), [data]);

  const handleSearch = useCallback(() => {
    setPage(1);
    const values = form.getFieldsValue();
    const sp = new URLSearchParams();
    const [start, end] = values.timeRange || [null, null];
    if (start) sp.set('start_time', String(start.valueOf()));
    if (end) sp.set('end_time', String(end.valueOf()));
    if (values.serviceName) sp.set('service_name', values.serviceName);
    if (values.status) sp.set('status', values.status);
    if (values.traceIdInput?.trim()) sp.set('trace_id', values.traceIdInput.trim());
    setSearchParams(sp);
  }, [form, setSearchParams]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
  };

  // Table columns (using backend fields)
  const columns: ColumnsType<TraceSearchResult> = [
    {
      title: 'TRACE ID',
      dataIndex: 'trace_id',
      width: 160,
      render: (id: string) => (
        <Tooltip title={id}>
          <span className={clsx('font-mono', styles.cellMono)}>{id.slice(0, 12)}…</span>
        </Tooltip>
      ),
    },
    {
      title: 'SERVICE',
      dataIndex: 'root_service',
      width: 120,
      render: (val: string | null) => (
        <span className={clsx('font-mono', styles.cellMono)}>{val || '-'}</span>
      ),
    },
    {
      title: 'OPERATION',
      dataIndex: 'root_operation',
      width: 160,
      ellipsis: true,
      render: (val: string | null) => (
        <Tooltip title={val || '-'}>
          <span className={clsx('font-mono', styles.cellMono)}>{val || '-'}</span>
        </Tooltip>
      ),
    },
    {
      title: 'DURATION',
      dataIndex: 'duration_ms',
      width: 100,
      sorter: (a, b) => a.duration_ms - b.duration_ms,
      render: (ms: number) => (
        <span className={clsx('font-mono', styles.cellMono)}>{formatDuration(ms)}</span>
      ),
    },
    {
      title: 'SPANS',
      dataIndex: 'span_count',
      width: 70,
      sorter: (a, b) => a.span_count - b.span_count,
      render: (n: number) => <span className={clsx('font-mono', styles.cellMono)}>{n}</span>,
    },
    {
      title: 'STATUS',
      dataIndex: 'status',
      width: 110,
      render: (s: string) => {
        const mapped = s === 'ok' ? 'success' : s === 'error' ? 'failure' : (s as 'success');
        return <OutcomeBadge outcome={mapped} />;
      },
    },
  ];

  const pagination: TablePaginationConfig = {
    current: page,
    pageSize: pageSize,
    total: data?.length ?? 0,
    showSizeChanger: false,
    size: 'small',
    onChange: p => setPage(p),
    showTotal: (total, range) => (
      <span className={clsx('font-mono', styles.cellMonoSm)}>
        {range[0]}-{range[1]} of {total.toLocaleString()}
      </span>
    ),
  };

  // ECharts option
  const histOption = mergeChartOption({
    xAxis: { type: 'category', data: histogram.bins },
    yAxis: { type: 'value', name: 'Traces' },
    series: [
      {
        type: 'bar',
        data: histogram.counts,
        itemStyle: { color: colors.brand, borderRadius: [3, 3, 0, 0] },
        barMaxWidth: 32,
      },
    ],
    grid: { top: 32, bottom: 36, left: 48, right: 16 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#2C2D42',
      borderColor: '#374151',
      textStyle: { color: colors.textPrimary, fontSize: fontSize.sm },
    },
  });

  return (
    <div className={styles.container}>
      {/* Page title */}
      <h1 className={styles.pageTitle}>Trace Search</h1>

      {/* Search form */}
      <Form
        form={form}
        component={false}
        initialValues={{
          serviceName: searchParams.get('service_name') || '',
          status: searchParams.get('status') || '',
          timeRange: [
            searchParams.get('start_time')
              ? dayjs(Number(searchParams.get('start_time')))
              : defaultStart,
            searchParams.get('end_time') ? dayjs(Number(searchParams.get('end_time'))) : now,
          ] as [dayjs.Dayjs | null, dayjs.Dayjs | null],
          traceIdInput: searchParams.get('trace_id') || '',
        }}
      >
        <div className={styles.searchForm}>
          <div>
            <div className={styles.formFieldLabel}>Time Range</div>
            <Form.Item name="timeRange" noStyle>
              <DatePicker.RangePicker showTime style={{ width: 360 }} />
            </Form.Item>
          </div>
          <div>
            <div className={styles.formFieldLabel}>Service</div>
            <Form.Item name="serviceName" noStyle>
              <Select
                style={{ width: 140 }}
                placeholder="All"
                allowClear
                options={[
                  { value: 'claude_code', label: 'claude_code' },
                  { value: 'openclaw', label: 'openclaw' },
                ]}
              />
            </Form.Item>
          </div>
          <div>
            <div className={styles.formFieldLabel}>Status</div>
            <Form.Item name="status" noStyle>
              <Select
                style={{ width: 110 }}
                placeholder="All"
                allowClear
                options={[
                  { value: 'ok', label: 'OK' },
                  { value: 'error', label: 'Error' },
                ]}
              />
            </Form.Item>
          </div>
          <div>
            <div className={styles.formFieldLabel}>Trace ID</div>
            <Form.Item name="traceIdInput" noStyle>
              <Input
                classNames={{ input: 'font-mono' }}
                style={{ width: 260 }}
                placeholder="Exact trace ID search"
                onKeyDown={handleKeyDown}
                allowClear
              />
            </Form.Item>
          </div>
          <Button
            type="primary"
            icon={<SearchOutlined />}
            onClick={handleSearch}
            className={styles.searchButton}
          >
            Search
          </Button>
        </div>
      </Form>

      {/* Summary bar */}
      <div className={clsx('font-mono', styles.summaryBar)}>
        <span>
          <strong className={styles.summaryValue}>{stats.total.toLocaleString()}</strong> traces
        </span>
        <span className={styles.summaryDivider}>|</span>
        <span>
          Error:{' '}
          <strong className={stats.errorPct > 5 ? styles.errorHighlight : styles.summaryValue}>
            {stats.errorPct.toFixed(2)}%
          </strong>
        </span>
        <span className={styles.summaryDivider}>|</span>
        <span>
          P50: <strong className={styles.summaryValue}>{formatDuration(stats.p50)}</strong>
        </span>
        <span>
          P99: <strong className={styles.summaryValue}>{formatDuration(stats.p99)}</strong>
        </span>
      </div>

      {/* Results area — left table, right chart */}
      <div className={styles.contentGrid}>
        {/* Left: table */}
        <div>
          <Table<TraceSearchResult>
            rowKey="trace_id"
            columns={columns}
            dataSource={paginatedData}
            loading={isLoading}
            pagination={pagination}
            size="small"
            onRow={record => ({
              onClick: () => navigate(`/traces/${record.trace_id}`),
              className: styles.tableRow,
            })}
            className={styles.tableContainer}
          />
        </div>

        {/* Right: histogram */}
        <div>
          <ChartPanel title="Duration Distribution">
            <ReactECharts
              echarts={echarts}
              option={histOption}
              className={styles.chartContainer}
              notMerge
              lazyUpdate
            />
          </ChartPanel>
        </div>
      </div>
    </div>
  );
}
