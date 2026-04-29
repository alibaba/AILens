import { useMemo, useCallback, useState } from 'react';
import clsx from 'clsx';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Table, Select, Tag, Spin, Tabs } from 'antd';
import type { TableProps } from 'antd';
import MetricCard from '../../components/shared/MetricCard';
import { fetchExperiments } from '../../api/experiments';
import { formatPct } from '../../utils/format';
import { useProjectStore } from '../../stores/project';
import type { ExperimentItem } from '../../types';
import styles from './styles.module.css';

// ── Format helpers ──

function formatNumber(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

// ── Main component ──

export default function ExperimentList() {
  const navigate = useNavigate();
  const currentProjectId = useProjectStore(s => s.currentProjectId);

  // Filters with project-based reset
  const [scaffoldFilter, setScaffoldFilter] = useState<string[]>([]);
  const [modelFilter, setModelFilter] = useState<string | undefined>(undefined);
  const [lastProjectId, setLastProjectId] = useState<string | null>(null);

  // Reset filters when project changes - using callback pattern
  const resetFilters = useCallback(() => {
    setScaffoldFilter([]);
    setModelFilter(undefined);
  }, []);

  // Track project changes and reset filters
  if (currentProjectId !== lastProjectId) {
    setLastProjectId(currentProjectId);
    if (lastProjectId !== null) {
      resetFilters();
    }
  }

  // Fetch experiments
  const { data, isLoading, isError } = useQuery({
    queryKey: ['experiments', currentProjectId],
    queryFn: () => fetchExperiments(currentProjectId!),
    enabled: !!currentProjectId,
    staleTime: 30_000,
  });

  const experiments = useMemo(() => data?.items ?? [], [data]);

  // Extract unique values for filter dropdowns
  const filterOptions = useMemo(() => {
    const scaffolds = new Set<string>();
    const models = new Set<string>();

    for (const exp of experiments) {
      if (exp.config.scaffolds) {
        for (const s of exp.config.scaffolds) scaffolds.add(s);
      }
      if (exp.config.model) models.add(exp.config.model);
    }

    return {
      scaffolds: [...scaffolds],
      models: [...models],
    };
  }, [experiments]);

  // Apply filters
  const filteredExperiments = useMemo(() => {
    return experiments.filter(exp => {
      if (scaffoldFilter.length > 0) {
        const expScaffolds = exp.config.scaffolds ?? [];
        if (!scaffoldFilter.some(sf => expScaffolds.includes(sf))) return false;
      }
      if (modelFilter && exp.config.model !== modelFilter) return false;
      return true;
    });
  }, [experiments, scaffoldFilter, modelFilter]);

  // KPI calculations
  const kpi = useMemo(() => {
    if (experiments.length === 0)
      return { total: 0, bestPassRate: 0, bestExpName: '', totalTokens: 0, totalTrajectories: 0 };

    let bestPassRate = 0;
    let bestExpName = '';
    let totalTokens = 0;
    let totalTrajectories = 0;

    for (const exp of experiments) {
      if (exp.pass_rate > bestPassRate) {
        bestPassRate = exp.pass_rate;
        bestExpName = exp.name;
      }
      totalTokens += exp.total_tokens;
      totalTrajectories += exp.total_trajectories;
    }

    return { total: experiments.length, bestPassRate, bestExpName, totalTokens, totalTrajectories };
  }, [experiments]);

  const handleRowClick = useCallback(
    (record: ExperimentItem) => {
      navigate(`/experiments/${record.id}`);
    },
    [navigate]
  );

  // Table columns
  const tableColumns: TableProps<ExperimentItem>['columns'] = useMemo(
    () => [
      {
        title: 'EXPERIMENT ID',
        dataIndex: 'name',
        key: 'name',
        sorter: (a, b) => a.name.localeCompare(b.name),
        render: (name: string) => <span className={styles.cellNameStrong}>{name}</span>,
      },
      {
        title: 'SCAFFOLDS',
        key: 'scaffolds',
        width: 160,
        render: (_: unknown, record: ExperimentItem) => {
          const scaffolds = record.config.scaffolds ?? [];
          return (
            <div className={styles.scaffoldTagRow}>
              {scaffolds.map(s => (
                <Tag key={s} className={styles.scaffoldTag}>
                  {s}
                </Tag>
              ))}
            </div>
          );
        },
      },
      {
        title: 'MODEL',
        dataIndex: ['config', 'model'],
        key: 'model',
        width: 120,
        render: (model: string) => (
          <span className={clsx('font-mono', styles.cellModel)}>{model}</span>
        ),
      },

      {
        title: 'MEAN REWARD',
        key: 'reward',
        width: 140,
        sorter: (a, b) => a.mean_reward - b.mean_reward,
        render: (_: unknown, record: ExperimentItem) => (
          <span className={clsx('font-mono', styles.cellMetric)}>
            {record.mean_reward.toFixed(2)}
          </span>
        ),
      },
      {
        title: 'PASS%',
        key: 'passRate',
        width: 100,
        sorter: (a, b) => a.pass_rate - b.pass_rate,
        render: (_: unknown, record: ExperimentItem) => (
          <span className={clsx('font-mono', styles.cellMetric)}>
            {formatPct(record.pass_rate)}
          </span>
        ),
      },
      {
        title: 'ITERATIONS',
        dataIndex: 'latest_iteration',
        key: 'iterations',
        width: 100,
        sorter: (a, b) => a.latest_iteration - b.latest_iteration,
        render: (val: number) => (
          <span className={clsx('font-mono', styles.cellMonoMuted)}>{val}</span>
        ),
      },
      {
        title: 'TRAJECTORIES',
        dataIndex: 'total_trajectories',
        key: 'trajectories',
        width: 120,
        sorter: (a, b) => a.total_trajectories - b.total_trajectories,
        render: (val: number) => (
          <span className={clsx('font-mono', styles.cellMonoMuted)}>{formatNumber(val)}</span>
        ),
      },
    ],
    []
  );

  if (!currentProjectId) {
    return <div className={styles.noProjectMessage}>Select a project to view experiments.</div>;
  }

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
        Failed to load experiments. Please check the backend connection.
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Page Title */}
      <h1 className={styles.pageTitle}>Experiment Dashboard</h1>

      {/* KPI Cards */}
      <div className={styles.kpiGrid}>
        <MetricCard title="Total Experiments" value={kpi.total} />
        <MetricCard title="Total Trajectories" value={formatNumber(kpi.totalTrajectories)} />
        <MetricCard
          title="Best Pass Rate"
          value={formatPct(kpi.bestPassRate)}
          subtitle={kpi.bestExpName}
        />
        <MetricCard
          title="Total Tokens"
          value={formatNumber(kpi.totalTokens)}
          subtitle={`≈$${((kpi.totalTokens / 1_000_000) * 0.1).toFixed(1)}K`}
        />
      </div>

      {/* Tabs: Experiments + Comparison */}
      <Tabs
        defaultActiveKey="experiments"
        items={[
          {
            key: 'experiments',
            label: '📋 Experiments',
            children: (
              <>
                {/* Filter Bar */}
                <div className={styles.filterBar}>
                  <Select
                    mode="multiple"
                    placeholder="Scaffold"
                    value={scaffoldFilter}
                    onChange={setScaffoldFilter}
                    allowClear
                    className={styles.selectStyle}
                    options={filterOptions.scaffolds.map(s => ({ value: s, label: s }))}
                    maxTagCount={1}
                  />
                  <Select
                    placeholder="Model"
                    value={modelFilter}
                    onChange={setModelFilter}
                    allowClear
                    className={styles.selectStyle}
                    options={filterOptions.models.map(m => ({ value: m, label: m }))}
                  />
                </div>

                {/* Experiment Table */}
                <Table<ExperimentItem>
                  dataSource={filteredExperiments}
                  columns={tableColumns}
                  rowKey="id"
                  pagination={{
                    pageSize: 20,
                    showSizeChanger: false,
                    showTotal: total => `${total} experiments`,
                  }}
                  sortDirections={['ascend', 'descend']}
                  onRow={record => ({
                    onClick: () => handleRowClick(record),
                    className: styles.tableRow,
                  })}
                  className={styles.experimentTable}
                />
              </>
            ),
          },
        ]}
        className={styles.tabsContainer}
      />
    </div>
  );
}
