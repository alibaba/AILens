import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Spin, Table, Tabs } from 'antd';
import type { TableProps } from 'antd';
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';

import { queryTraceQL } from '../../api/traceql';
import { buildDatasetSummaryQuery } from '../../queries/dataset';
import { formatPct } from '../../utils/format';
import styles from './styles.module.css';

interface DatasetRow {
  dataset_name: string;
  task_count: number;
  experiment_count: number;
  total_trajectories: number;
  pass_rate: number;
}

function toDatasetRow(row: Record<string, unknown>): DatasetRow {
  return {
    dataset_name: String(row.dataset_name ?? ''),
    task_count: Number(row.task_count ?? 0),
    experiment_count: Number(row.experiment_count ?? 0),
    total_trajectories: Number(row.trajectory_count ?? 0),
    pass_rate: Number(row.pass_rate ?? 0),
  };
}

export default function DatasetList() {
  const navigate = useNavigate();

  const query = useMemo(() => buildDatasetSummaryQuery(), []);

  const {
    data: rows,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['datasets', query],
    queryFn: () => queryTraceQL(query),
    staleTime: 60_000,
  });

  const datasets = useMemo<DatasetRow[]>(() => {
    if (!rows || rows.length === 0) return [];
    return rows
      .map(toDatasetRow)
      .filter(d => d.dataset_name)
      .sort((a, b) => a.dataset_name.localeCompare(b.dataset_name));
  }, [rows]);

  const dashboardStats = useMemo(() => {
    const totalDatasets = datasets.length;
    const totalTasks = datasets.reduce((sum, d) => sum + d.task_count, 0);
    const totalExperiments = datasets.reduce((sum, d) => sum + d.experiment_count, 0);
    const totalTrajectories = datasets.reduce((sum, d) => sum + d.total_trajectories, 0);
    const bestPassRate = datasets.length > 0 ? Math.max(...datasets.map(d => d.pass_rate)) : 0;
    return { totalDatasets, totalTasks, totalExperiments, totalTrajectories, bestPassRate };
  }, [datasets]);

  const handleRowClick = useCallback(
    (record: DatasetRow) => {
      navigate(`/datasets/${encodeURIComponent(record.dataset_name)}/tasks`);
    },
    [navigate]
  );

  const tableColumns: TableProps<DatasetRow>['columns'] = useMemo(
    () => [
      {
        title: 'DATASET',
        dataIndex: 'dataset_name',
        key: 'dataset_name',
        sorter: (a, b) => a.dataset_name.localeCompare(b.dataset_name),
        render: (name: string) => <span className={styles.cellNameStrong}>{name}</span>,
      },
      {
        title: 'TASKS',
        dataIndex: 'task_count',
        key: 'task_count',
        width: 100,
        sorter: (a, b) => a.task_count - b.task_count,
        render: (val: number) => (
          <span className={clsx('font-mono', styles.cellMetric)}>{val}</span>
        ),
      },
      {
        title: 'EXPERIMENTS',
        dataIndex: 'experiment_count',
        key: 'experiment_count',
        width: 140,
        sorter: (a, b) => a.experiment_count - b.experiment_count,
        render: (val: number) => (
          <span className={clsx('font-mono', styles.cellMetric)}>{val}</span>
        ),
      },
      {
        title: 'TRAJECTORIES',
        dataIndex: 'total_trajectories',
        key: 'total_trajectories',
        width: 140,
        sorter: (a, b) => a.total_trajectories - b.total_trajectories,
        render: (val: number) => (
          <span className={clsx('font-mono', styles.cellMetric)}>{val.toLocaleString()}</span>
        ),
      },
      {
        title: 'PASS RATE',
        dataIndex: 'pass_rate',
        key: 'pass_rate',
        width: 120,
        sorter: (a, b) => a.pass_rate - b.pass_rate,
        render: (val: number) => (
          <span className={clsx('font-mono', styles.cellMetric)}>{formatPct(val)}</span>
        ),
      },
    ],
    []
  );

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <Spin size="large" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className={styles.errorMessage}>
        Failed to load datasets. Please check the backend connection.
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h1 className={styles.pageTitle}>Datasets Dashboard</h1>

      {/* Dashboard */}
      <div className={styles.summaryCard}>
        <div className={styles.summaryStats}>
          <div className={styles.statItem}>
            <span className={styles.statLabel}>TOTAL DATASETS</span>
            <span className={styles.statValue}>
              {dashboardStats.totalDatasets.toLocaleString()}
            </span>
          </div>
          <div className={styles.statDivider} />
          <div className={styles.statItem}>
            <span className={styles.statLabel}>TOTAL TASKS</span>
            <span className={styles.statValue}>{dashboardStats.totalTasks.toLocaleString()}</span>
          </div>
          <div className={styles.statDivider} />
          <div className={styles.statItem}>
            <span className={styles.statLabel}>TOTAL EXPERIMENTS</span>
            <span className={styles.statValue}>
              {dashboardStats.totalExperiments.toLocaleString()}
            </span>
          </div>
          <div className={styles.statDivider} />
          <div className={styles.statItem}>
            <span className={styles.statLabel}>TOTAL TRAJECTORIES</span>
            <span className={styles.statValue}>
              {dashboardStats.totalTrajectories.toLocaleString()}
            </span>
          </div>
          <div className={styles.statDivider} />
          <div className={styles.statItem}>
            <span className={styles.statLabel}>BEST PASS RATE</span>
            <span className={styles.statValue}>{formatPct(dashboardStats.bestPassRate)}</span>
          </div>
        </div>
      </div>

      <Tabs
        defaultActiveKey="datasets"
        items={[
          {
            key: 'datasets',
            label: '📋 Datasets',
            children: (
              <Table<DatasetRow>
                dataSource={datasets}
                columns={tableColumns}
                rowKey="dataset_name"
                pagination={{
                  pageSize: 20,
                  showSizeChanger: false,
                  showTotal: total => `${total} datasets`,
                }}
                sortDirections={['ascend', 'descend']}
                onRow={record => ({
                  onClick: () => handleRowClick(record),
                  className: styles.tableRow,
                })}
                className={styles.datasetTable}
              />
            ),
          },
        ]}
        className={styles.tabsContainer}
      />
    </div>
  );
}
