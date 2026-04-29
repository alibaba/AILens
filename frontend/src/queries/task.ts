// src/queries/task.ts

// ── Task Summary Query (TaskLibrary) ──

const TASK_SUMMARY_SELECT = [
  'task_id',
  'task_language',
  'count() as trajectory_count',
  'count_distinct(experiment_id) as experiment_count',
  "sum(if(verify_code='success', 1, 0)) as pass_count",
  "sum(if(verify_code='failure', 1, 0)) as fail_count",
  "round(avg(if(verify_code='success', 1, 0)), 4) as pass_rate",
  'max(turns) as max_turns',
  'min(turns) as min_turns',
  'round(avg(turns), 2) as avg_turns',
  'max(duration_ms) as max_duration_ms',
  'min(duration_ms) as min_duration_ms',
  'round(avg(duration_ms), 0) as avg_duration_ms',
];

const TASK_SUMMARY_BY = ['task_id'];

/**
 * Builds a TraceQL aggregation query for the Task Library page.
 * Groups by task_id; supports optional language and outcome selector filters.
 */
export function buildTaskSummaryQuery(filters: { language?: string; outcome?: string[] }): string {
  const conditions: string[] = [];
  if (filters.language) conditions.push(`task_language="${filters.language}"`);
  if (filters.outcome?.length === 1) {
    conditions.push(`verify_code="${filters.outcome[0]}"`);
  } else if (filters.outcome && filters.outcome.length > 1) {
    const or = filters.outcome.map(o => `verify_code="${o}"`).join(' or ');
    conditions.push(`(${or})`);
  }
  const selector = conditions.length > 0 ? `{${conditions.join(' and ')}}` : '{}';
  return (
    `${selector}\n` +
    `| select(${TASK_SUMMARY_SELECT.join(', ')})\n` +
    `  by (${TASK_SUMMARY_BY.join(', ')})`
  );
}

// ── Task By Experiment Query (TaskDetail) ──

const TASK_BY_EXP_SELECT = [
  'task_id',
  'task_language',
  'experiment_id',
  'count() as trajectory_count',
  "sum(if(verify_code='success', 1, 0)) as pass_count",
  "sum(if(verify_code='failure', 1, 0)) as fail_count",
  "round(avg(if(verify_code='success', 1, 0)), 4) as pass_rate",
  'max(turns) as max_turns',
  'min(turns) as min_turns',
  'round(avg(turns), 2) as avg_turns',
  'max(duration_ms) as max_duration_ms',
  'min(duration_ms) as min_duration_ms',
  'round(avg(duration_ms), 0) as avg_duration_ms',
];

const TASK_BY_EXP_BY = ['task_id', 'experiment_id'];

/**
 * Builds a TraceQL aggregation query for the Task Detail page.
 * Groups trajectories for the given task_id by experiment_id.
 */
export function buildTaskByExperimentQuery(taskId: string): string {
  return (
    `{task_id="${taskId}"}\n` +
    `| select(${TASK_BY_EXP_SELECT.join(', ')})\n` +
    `  by (${TASK_BY_EXP_BY.join(', ')})`
  );
}
