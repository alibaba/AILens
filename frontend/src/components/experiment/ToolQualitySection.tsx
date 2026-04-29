import { useMemo } from 'react';
import clsx from 'clsx';
import { Table } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { ToolQualityItem, ToolLatencyItem } from '../../types';
import { formatPct } from '../../utils/format';
import styles from './ToolQualitySection.module.css';

interface Props {
  data: ToolQualityItem[];
  latencyData?: ToolLatencyItem[];
}

type RateTier = 'Low' | 'Mid' | 'High';

function successRateTier(rate: number): RateTier {
  if (rate < 0.8) return 'Low';
  if (rate < 0.95) return 'Mid';
  return 'High';
}

interface MergedItem extends ToolQualityItem {
  avg_ms?: number;
  p50_ms?: number;
  p99_ms?: number;
}

export default function ToolQualitySection({ data, latencyData }: Props) {
  const mergedData = useMemo(() => {
    if (!latencyData) return data;
    const latencyMap = new Map(latencyData.map(item => [item.tool, item]));
    return data.map(item => {
      const latency = latencyMap.get(item.tool);
      return latency
        ? { ...item, avg_ms: latency.avg_ms, p50_ms: latency.p50_ms, p99_ms: latency.p99_ms }
        : item;
    }) as MergedItem[];
  }, [data, latencyData]);

  const dataWithTotal = useMemo(() => {
    if (mergedData.length === 0) return [];
    const totalCalls = mergedData.reduce((s, d) => s + d.call_count, 0);
    const total: MergedItem = {
      tool: '合计',
      scaffold: '',
      call_count: totalCalls,
      success_rate:
        totalCalls > 0
          ? mergedData.reduce((s, d) => s + d.success_rate * d.call_count, 0) / totalCalls
          : 0,
      error_task_pct: mergedData.reduce((s, d) => s + d.error_task_pct, 0) / mergedData.length,
      success_task_pct: mergedData.reduce((s, d) => s + d.success_task_pct, 0) / mergedData.length,
      trajectory_count: mergedData.reduce((s, d) => s + d.trajectory_count, 0),
      at_least_one_error_task_rate:
        mergedData.reduce((s, d) => s + (d.at_least_one_error_task_rate ?? 0), 0) /
        mergedData.length,
      at_least_one_success_task_rate:
        mergedData.reduce((s, d) => s + (d.at_least_one_success_task_rate ?? 0), 0) /
        mergedData.length,
    };
    return [...mergedData, total];
  }, [mergedData]);

  const columns: ColumnsType<MergedItem> = [
    {
      title: 'Tool',
      dataIndex: 'tool',
      key: 'tool',
      width: 130,
      render: (v: string) => (
        <span
          className={clsx({
            [styles.toolNameTotal]: v === '合计',
            [styles.toolNameMono]: v !== '合计',
          })}
        >
          {v}
        </span>
      ),
    },
    { title: 'Scaffold', dataIndex: 'scaffold', key: 'scaffold', width: 120 },
    {
      title: '调用次数',
      dataIndex: 'call_count',
      key: 'call_count',
      width: 100,
      sorter: (a, b) => a.call_count - b.call_count,
      render: (v: number) => <span className="font-mono">{v}</span>,
    },
    {
      title: 'Avg(ms)',
      dataIndex: 'avg_ms',
      key: 'avg_ms',
      width: 90,
      sorter: (a, b) => (a.avg_ms ?? 0) - (b.avg_ms ?? 0),
      render: (v: number | undefined) => (
        <span className="font-mono">{v !== undefined ? Math.round(v) : '-'}</span>
      ),
    },
    {
      title: 'P50(ms)',
      dataIndex: 'p50_ms',
      key: 'p50_ms',
      width: 90,
      sorter: (a, b) => (a.p50_ms ?? 0) - (b.p50_ms ?? 0),
      render: (v: number | undefined) => (
        <span className="font-mono">{v !== undefined ? Math.round(v) : '-'}</span>
      ),
    },
    {
      title: 'P99(ms)',
      dataIndex: 'p99_ms',
      key: 'p99_ms',
      width: 90,
      sorter: (a, b) => (a.p99_ms ?? 0) - (b.p99_ms ?? 0),
      render: (v: number | undefined, record: MergedItem) => {
        if (v === undefined) return '-';
        const isHigh = record.avg_ms && v > record.avg_ms * 3;
        return (
          <span className={clsx(styles.p99Mono, { [styles.p99High]: isHigh })}>
            {Math.round(v)}
          </span>
        );
      },
    },
    {
      title: '成功率',
      dataIndex: 'success_rate',
      key: 'success_rate',
      width: 100,
      defaultSortOrder: 'ascend',
      sorter: (a, b) => a.success_rate - b.success_rate,
      render: (v: number) => {
        const tier = successRateTier(v);
        return (
          <span
            className={clsx(styles.ratePill, {
              [styles.rateTierLow]: tier === 'Low',
              [styles.rateTierMid]: tier === 'Mid',
              [styles.rateTierHigh]: tier === 'High',
            })}
          >
            {formatPct(v)}
          </span>
        );
      },
    },
    {
      title: '≥1次错误任务占比',
      dataIndex: 'error_task_pct',
      key: 'error_task_pct',
      width: 150,
      sorter: (a, b) => a.error_task_pct - b.error_task_pct,
      render: (v: number) => <span className="font-mono">{formatPct(v)}</span>,
    },
    {
      title: '≥1次成功任务占比',
      dataIndex: 'success_task_pct',
      key: 'success_task_pct',
      width: 150,
      sorter: (a, b) => a.success_task_pct - b.success_task_pct,
      render: (v: number) => <span className="font-mono">{formatPct(v)}</span>,
    },
    {
      title: '≥1 Error Task %',
      dataIndex: 'at_least_one_error_task_rate',
      key: 'at_least_one_error_task_rate',
      width: 140,
      sorter: (a, b) =>
        (a.at_least_one_error_task_rate ?? 0) - (b.at_least_one_error_task_rate ?? 0),
      render: (v: number) => (
        <span className="font-mono">{v !== undefined ? formatPct(v) : '-'}</span>
      ),
    },
    {
      title: '≥1 Success Task %',
      dataIndex: 'at_least_one_success_task_rate',
      key: 'at_least_one_success_task_rate',
      width: 150,
      sorter: (a, b) =>
        (a.at_least_one_success_task_rate ?? 0) - (b.at_least_one_success_task_rate ?? 0),
      render: (v: number) => (
        <span className="font-mono">{v !== undefined ? formatPct(v) : '-'}</span>
      ),
    },
  ];

  return (
    <div className={styles.panel}>
      <Table<MergedItem>
        columns={columns}
        dataSource={dataWithTotal}
        rowKey={record => `${record.tool}-${record.scaffold}`}
        size="small"
        pagination={false}
        rowClassName={record => (record.tool === '合计' ? 'summary-row' : '')}
      />
    </div>
  );
}
