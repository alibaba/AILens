import { useMemo, useState } from 'react';
import clsx from 'clsx';
import { Progress, Table, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import ChartPanel from '../shared/ChartPanel';
import { colors } from '../../styles/theme';
import type { LanguageStatsItem } from '../../types';
import { formatDuration, formatPct } from '../../utils/format';

interface Props {
  data: LanguageStatsItem[];
}

export default function LanguageStatsSection({ data }: Props) {
  const [selectedRow, setSelectedRow] = useState<string | null>(null);

  const totalRow = useMemo<LanguageStatsItem | null>(() => {
    if (data.length === 0) return null;
    const totalCount = data.reduce((s, d) => s + d.count, 0);
    if (totalCount === 0) return null;
    return {
      language: 'Total',
      count: totalCount,
      pass_rate: data.reduce((s, d) => s + d.pass_rate * d.count, 0) / totalCount,
      max_turns_passed: Math.max(...data.map(d => d.max_turns_passed)),
      avg_turns_passed: data.reduce((s, d) => s + d.avg_turns_passed * d.count, 0) / totalCount,
      max_duration_passed_ms: Math.max(...data.map(d => d.max_duration_passed_ms)),
      avg_duration_passed_ms:
        data.reduce((s, d) => s + d.avg_duration_passed_ms * d.count, 0) / totalCount,
    };
  }, [data]);

  const passRateColor = (v: number) =>
    v < 0.4 ? colors.error : v < 0.7 ? colors.warning : colors.success;

  const passRateTextClass = (v: number) =>
    v < 0.4 ? 'text-failure' : v < 0.7 ? 'text-warning' : 'text-success';

  const columns: ColumnsType<LanguageStatsItem> = [
    {
      title: 'Language',
      dataIndex: 'language',
      key: 'language',
      width: 100,
      render: (v: string) => <Tag>{v}</Tag>,
    },
    {
      title: 'Trajectories',
      dataIndex: 'count',
      key: 'count',
      width: 90,
      sorter: (a, b) => a.count - b.count,
      render: (v: number) => <span className="font-mono">{v.toLocaleString()}</span>,
    },
    {
      title: 'Pass Rate',
      dataIndex: 'pass_rate',
      key: 'pass_rate',
      width: 160,
      defaultSortOrder: 'descend',
      sorter: (a, b) => a.pass_rate - b.pass_rate,
      render: (v: number) => (
        <div className="flex items-center gap-2">
          <div className="min-w-[60px] flex-1">
            <Progress
              percent={Math.round(v * 100)}
              size="small"
              showInfo={false}
              strokeColor={passRateColor(v)}
              trailColor="rgba(255,255,255,0.08)"
            />
          </div>
          <span className={clsx('font-mono min-w-[48px] text-right', passRateTextClass(v))}>
            {formatPct(v)}
          </span>
        </div>
      ),
    },
    {
      title: 'Avg Turns',
      dataIndex: 'avg_turns_passed',
      key: 'avg_turns_passed',
      width: 90,
      sorter: (a, b) => a.avg_turns_passed - b.avg_turns_passed,
      render: (v: number) => <span className="font-mono">{v.toFixed(1)}</span>,
    },
    {
      title: 'Max Turns',
      dataIndex: 'max_turns_passed',
      key: 'max_turns_passed',
      width: 90,
      sorter: (a, b) => a.max_turns_passed - b.max_turns_passed,
      render: (v: number) => <span className="font-mono">{v}</span>,
    },
    {
      title: 'Avg Duration',
      dataIndex: 'avg_duration_passed_ms',
      key: 'avg_duration_passed_ms',
      width: 110,
      sorter: (a, b) => a.avg_duration_passed_ms - b.avg_duration_passed_ms,
      render: (v: number) => <span className="font-mono">{formatDuration(v)}</span>,
    },
    {
      title: 'Max Duration',
      dataIndex: 'max_duration_passed_ms',
      key: 'max_duration_passed_ms',
      width: 110,
      sorter: (a, b) => a.max_duration_passed_ms - b.max_duration_passed_ms,
      render: (v: number) => <span className="font-mono">{formatDuration(v)}</span>,
    },
  ];

  return (
    <ChartPanel title="Language Stats">
      <Table<LanguageStatsItem>
        columns={columns}
        dataSource={data}
        rowKey="language"
        size="small"
        pagination={false}
        onRow={record => ({
          onClick: () => setSelectedRow(record.language === selectedRow ? null : record.language),
          className: clsx(
            'cursor-pointer',
            record.language === selectedRow && 'bg-[var(--color-background-hover)]'
          ),
        })}
        summary={() => {
          if (!totalRow) return null;
          return (
            <Table.Summary fixed="bottom">
              <Table.Summary.Row className="bg-input font-bold">
                <Table.Summary.Cell index={0}>Total</Table.Summary.Cell>
                <Table.Summary.Cell index={1}>
                  <span className="font-mono">{totalRow.count.toLocaleString()}</span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={2}>
                  <div className="flex items-center gap-2">
                    <div className="min-w-[60px] flex-1">
                      <Progress
                        percent={Math.round(totalRow.pass_rate * 100)}
                        size="small"
                        showInfo={false}
                        strokeColor={passRateColor(totalRow.pass_rate)}
                        trailColor="rgba(255,255,255,0.08)"
                      />
                    </div>
                    <span
                      className={clsx(
                        'font-mono min-w-[48px] text-right',
                        passRateTextClass(totalRow.pass_rate)
                      )}
                    >
                      {formatPct(totalRow.pass_rate)}
                    </span>
                  </div>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={3}>
                  <span className="font-mono">{totalRow.avg_turns_passed.toFixed(1)}</span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={4}>
                  <span className="font-mono">{totalRow.max_turns_passed}</span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={5}>
                  <span className="font-mono">
                    {formatDuration(totalRow.avg_duration_passed_ms)}
                  </span>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={6}>
                  <span className="font-mono">
                    {formatDuration(totalRow.max_duration_passed_ms)}
                  </span>
                </Table.Summary.Cell>
              </Table.Summary.Row>
            </Table.Summary>
          );
        }}
      />
    </ChartPanel>
  );
}
