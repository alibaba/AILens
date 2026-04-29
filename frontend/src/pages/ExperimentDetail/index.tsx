// Experiment Detail Page - Main entry point with Tab layout

import { useEffect, useState, useMemo } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Form, Spin, Tabs } from 'antd';
import { fetchExperiment } from '../../api/experiments';
import { fetchLanguages, fetchToolSchemas, fetchIterations } from '../../api/stats';
import ExperimentHeader from '../experiment-detail/components/shared/ExperimentHeader';
import {
  toExperimentQueryFilters,
  type ExperimentFilterFormValues,
} from '../experiment-detail/components/shared/experimentFilterForm';
import {
  TrainingOverviewTab,
  TaskAnalysisTab,
  BehaviorAnalysisTab,
  QualityAssessmentTab,
} from '../experiment-detail';
import { useExperimentStore } from '../../stores/experiment';
import styles from './styles.module.css';

// ── URL TabKey -> Tab key mapping ──
const getTabFromTabKey = (tabKey?: string): string => {
  switch (tabKey) {
    case 'training-overview':
      return 'training';
    case 'task-analysis':
      return 'task';
    case 'trajectory-explorer':
      return 'behavior';
    case 'settings':
      return 'quality';
    default:
      return 'training'; // 默认第一个tab
  }
};

// ── URL Path <-> Tab key mapping (for backward compatibility) ──
const getTabFromPath = (path: string): string => {
  if (path.endsWith('/training-overview')) return 'training';
  if (path.endsWith('/task-analysis')) return 'task';
  if (path.endsWith('/trajectory-explorer')) return 'behavior';
  if (path.endsWith('/settings')) return 'quality';
  return 'training'; // 默认第一个tab
};

const getPathFromTab = (baseUrl: string, tabKey: string): string => {
  switch (tabKey) {
    case 'training':
      return `${baseUrl}/training-overview`;
    case 'task':
      return `${baseUrl}/task-analysis`;
    case 'behavior':
      return `${baseUrl}/trajectory-explorer`;
    case 'quality':
      return `${baseUrl}/settings`;
    default:
      return `${baseUrl}/training-overview`;
  }
};

// ── Hash <-> Tab key mapping (保持向后兼容) ──
const getTabFromHash = (hash: string): string => {
  switch (hash) {
    case '#training-overview':
      return 'training';
    case '#task-analysis':
      return 'task';
    case '#trajectory-explorer':
      return 'behavior';
    case '#settings':
      return 'quality';
    default:
      return 'training'; // 默认第一个tab
  }
};

export default function ExperimentDetail() {
  const { id, tabKey } = useParams<{ id: string; tabKey?: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const setCurrentExperiment = useExperimentStore(s => s.setCurrentExperiment);

  // ── Data fetching ──
  const { data: experiment, isLoading: expLoading } = useQuery({
    queryKey: ['experiment', id],
    queryFn: () => fetchExperiment(id!),
    enabled: !!id,
    staleTime: 30_000,
  });

  const { data: languagesData } = useQuery({
    queryKey: ['experimentLanguages', id],
    queryFn: () => fetchLanguages(id!),
    enabled: !!id,
    staleTime: 60_000,
  });

  const { data: toolSchemasData } = useQuery({
    queryKey: ['experimentToolSchemas', id],
    queryFn: () => fetchToolSchemas(id!),
    enabled: !!id,
    staleTime: 60_000,
  });

  // ── Global filters (single Form instance, shared by header + tabs) ──
  const [filterForm] = Form.useForm<ExperimentFilterFormValues>();
  const filterFormValues = Form.useWatch([], filterForm);
  const { splitBy, scaffoldFilter, languageFilter, toolSchemaFilter } = useMemo(
    () => toExperimentQueryFilters(filterFormValues),
    [filterFormValues]
  );

  // Filter form: no reset on `id` — product flow leaves this page then opens another experiment from
  // the list, so the route remounts and ExperimentHeader `initialValues` apply fresh. If you add
  // in-place navigation between experiments (same mount, only `id` changes), call filterForm.resetFields() on id change.

  // ── Iteration filter (shown only on Task Analysis tab) ──
  const [iterationFilter, setIterationFilter] = useState<string>('all');

  const { data: iterationsData } = useQuery({
    queryKey: ['experimentIterations', id],
    queryFn: () => fetchIterations(id!),
    staleTime: 60_000,
    enabled: !!id,
  });

  const iterationOptions = useMemo(() => {
    const items = iterationsData?.items ?? [];
    return [
      { label: 'All', value: 'all' },
      ...items.map(item => ({
        label: `#${item.iteration_num}`,
        value: String(item.iteration_num),
      })),
    ];
  }, [iterationsData]);

  // Derive activeTab from URL tabKey parameter, or fallback to path/hash (优先tabKey参数，然后路径，最后hash)
  const activeTab = tabKey
    ? getTabFromTabKey(tabKey)
    : location.hash
      ? getTabFromHash(location.hash)
      : getTabFromPath(location.pathname);

  // Sync experiment info to global store for TopBar display
  useEffect(() => {
    if (experiment) {
      setCurrentExperiment({
        name: experiment.name,
        status: experiment.status,
        scaffolds: experiment.config.scaffolds ?? [],
        model: experiment.config.model,
      });
    }
    return () => setCurrentExperiment(null);
  }, [experiment, setCurrentExperiment]);

  if (expLoading) {
    return <LoadingSpinner />;
  }

  if (!experiment) {
    return <NotFound />;
  }

  const scaffolds = experiment.config.scaffolds ?? [];
  const languages = languagesData?.languages ?? [];
  const toolSchemas = toolSchemasData?.tool_schemas ?? [];

  // Handle tab change with URL path sync (优先路径格式)
  const handleTabChange = (tabKey: string) => {
    const baseUrl = `/experiments/${id}`;
    const newPath = getPathFromTab(baseUrl, tabKey);
    // Update URL path (using replace to avoid excessive history entries)
    navigate(newPath, { replace: true });
  };

  return (
    <div className={styles.page}>
      <ExperimentHeader
        form={filterForm}
        scaffolds={scaffolds}
        languages={languages}
        toolSchemas={toolSchemas}
        showIterationFilter={activeTab === 'task'}
        iterationFilter={iterationFilter}
        iterationOptions={iterationOptions}
        onIterationChange={setIterationFilter}
      />

      <Tabs
        activeKey={activeTab}
        onChange={handleTabChange}
        items={[
          {
            key: 'training',
            label: '📈 Overview',
            children: (
              <TrainingOverviewTab
                experimentId={id!}
                splitBy={splitBy}
                scaffoldFilter={scaffoldFilter}
                languageFilter={languageFilter}
                toolSchemaFilter={toolSchemaFilter}
                isActive={activeTab === 'training'}
              />
            ),
          },
          {
            key: 'task',
            label: '🎯 Task Analysis',
            children: (
              <TaskAnalysisTab
                experimentId={id!}
                scaffoldFilter={scaffoldFilter}
                languageFilter={languageFilter}
                toolSchemaFilter={toolSchemaFilter}
                iterationFilter={iterationFilter}
                isActive={activeTab === 'task'}
              />
            ),
          },
          {
            key: 'behavior',
            label: '🤖 Behavior Analysis',
            children: <BehaviorAnalysisTab />,
          },
          {
            key: 'quality',
            label: '⚖️ Quality Assessment',
            children: <QualityAssessmentTab isActive={activeTab === 'quality'} />,
          },
        ]}
        className={styles.tabsPanel}
      />
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className={styles.loadingWrap}>
      <Spin size="large" />
    </div>
  );
}

function NotFound() {
  return <div className={styles.notFound}>Experiment not found.</div>;
}
