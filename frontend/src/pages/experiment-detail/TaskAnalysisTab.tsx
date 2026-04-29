// Task Analysis Tab - Stats summary, language stats, task difficulty, pass rate & turns trends

import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Spin } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import LanguageStatsSection from '../../components/experiment/LanguageStatsSection';
import TaskDifficultySection from '../../components/experiment/TaskDifficultySection';
import TaskPassRateTrendSection from '../../components/experiment/TaskPassRateTrendSection';
import TaskTurnsTrendSection from '../../components/experiment/TaskTurnsTrendSection';
import { useLanguageStats } from '../../hooks/useLanguageStats';
import { useTaskEffectiveness } from '../../hooks/useTaskEffectiveness';
import { buildFilterParams, buildFilterQueryString } from './helpers';
import { formatPct } from '../../utils/format';
import { colors } from '../../styles/theme';
import styles from './styles.module.css';

interface TaskAnalysisTabProps {
  experimentId: string;
  scaffoldFilter: string | undefined;
  languageFilter: string | undefined;
  toolSchemaFilter: string | undefined;
  iterationFilter: string;
  isActive: boolean;
}

export default function TaskAnalysisTab({
  experimentId,
  scaffoldFilter,
  languageFilter,
  toolSchemaFilter,
  iterationFilter,
  isActive,
}: TaskAnalysisTabProps) {
  const navigate = useNavigate();

  const filterParams = useMemo(() => {
    const iteration = iterationFilter !== 'all' ? Number(iterationFilter) : undefined;
    return buildFilterParams(scaffoldFilter, languageFilter, toolSchemaFilter, iteration);
  }, [scaffoldFilter, languageFilter, toolSchemaFilter, iterationFilter]);

  const { data: langStats, isLoading: langLoading } = useLanguageStats(experimentId, filterParams, {
    enabled: isActive,
  });

  const { data: taskData, isLoading: taskStatsLoading } = useTaskEffectiveness(
    experimentId,
    filterParams,
    { enabled: isActive }
  );

  const summaryStats = useMemo(() => {
    const tasks = taskData?.tasks ?? [];
    let trajectoryTotal = 0;
    let passTotal = 0;
    let failTotal = 0;
    for (const t of tasks) {
      trajectoryTotal += t.rollout_count;
      passTotal += t.pass_count;
      failTotal += t.fail_count;
    }
    const taskCount = tasks.length;
    const passRate = trajectoryTotal > 0 ? passTotal / trajectoryTotal : 0;
    return { taskCount, trajectoryTotal, passTotal, failTotal, passRate };
  }, [taskData]);

  if (langLoading) {
    return (
      <div className={styles.loadingContainer}>
        <Spin size="large" />
        <div className={styles.loadingText}>Loading task analysis...</div>
      </div>
    );
  }

  return (
    <div className={styles.taskContainer}>
      {/* Summary Stats */}
      <div className={styles.taskSummaryWrapper}>
        <div className={styles.taskSummaryHeader}>
          <Button
            type="link"
            size="small"
            onClick={() =>
              navigate(
                `/experiments/${experimentId}/tasks${buildFilterQueryString(scaffoldFilter, languageFilter, toolSchemaFilter, iterationFilter)}`
              )
            }
            className={styles.taskSeeAllLink}
          >
            See all Tasks →
          </Button>
        </div>
        <div className={styles.taskSummaryCard}>
          <div className={styles.taskSummaryStats}>
            <div className={styles.taskStatItem}>
              <span className={styles.taskStatLabel}>Total Tasks</span>
              <span className={styles.taskStatValue}>
                {taskStatsLoading ? <Spin size="small" /> : summaryStats.taskCount.toLocaleString()}
              </span>
            </div>
            <div className={styles.taskStatDivider} />
            <div className={styles.taskStatItem}>
              <span className={styles.taskStatLabel}>Total Trajectories</span>
              <span className={styles.taskStatValue}>
                {taskStatsLoading ? (
                  <Spin size="small" />
                ) : (
                  summaryStats.trajectoryTotal.toLocaleString()
                )}
              </span>
            </div>
            <div className={styles.taskStatDivider} />
            <div className={styles.taskStatItem}>
              <span className={styles.taskStatLabel}>Pass / Fail</span>
              <span className={styles.taskStatValue}>
                {taskStatsLoading ? (
                  <Spin size="small" />
                ) : (
                  <>
                    <CheckCircleOutlined style={{ color: colors.success, marginRight: 4 }} />
                    <span style={{ color: colors.success }}>
                      {summaryStats.passTotal.toLocaleString()}
                    </span>
                    <span className={styles.taskStatSep}>/</span>
                    <CloseCircleOutlined style={{ color: colors.error, marginRight: 4 }} />
                    <span style={{ color: colors.error }}>
                      {summaryStats.failTotal.toLocaleString()}
                    </span>
                  </>
                )}
              </span>
            </div>
            <div className={styles.taskStatDivider} />
            <div className={styles.taskStatItem}>
              <span className={styles.taskStatLabel}>Pass Rate</span>
              <span className={styles.taskStatValue}>
                {taskStatsLoading ? (
                  <Spin size="small" />
                ) : (
                  <span
                    style={{
                      color:
                        summaryStats.passRate >= 0.7
                          ? colors.success
                          : summaryStats.passRate >= 0.4
                            ? colors.warning
                            : colors.error,
                    }}
                  >
                    {formatPct(summaryStats.passRate)}
                  </span>
                )}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Language Stats + Task Difficulty Distribution side by side */}
      <div className={styles.statsGrid}>
        {langStats && langStats.length > 0 && <LanguageStatsSection data={langStats} />}
        <TaskDifficultySection
          experimentId={experimentId}
          filterParams={filterParams}
          isActive={isActive}
        />
      </div>

      {/* Task Pass Rate Trend */}
      <TaskPassRateTrendSection
        experimentId={experimentId}
        filterParams={filterParams}
        isActive={isActive}
      />

      {/* Task Turns Trend */}
      <TaskTurnsTrendSection
        experimentId={experimentId}
        filterParams={filterParams}
        isActive={isActive}
      />
    </div>
  );
}
