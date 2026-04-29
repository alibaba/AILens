// src/queries/dataset.ts

// ── Dataset Summary Query ──
// Aggregates trajectory stats grouped by dataset_name.

const DATASET_SUMMARY_SELECT = [
  'dataset_name',
  'count() as trajectory_count',
  'count_distinct(task_id) as task_count',
  'count_distinct(experiment_id) as experiment_count',
  "sum(if(verify_code='success', 1, 0)) as pass_count",
  "sum(if(verify_code='failure', 1, 0)) as fail_count",
  "round(avg(if(verify_code='success', 1, 0)), 4) as pass_rate",
];

const DATASET_SUMMARY_BY = ['dataset_name'];

/**
 * Builds a TraceQL aggregation query for the Dataset List page.
 * Groups trajectories by dataset_name to produce per-dataset stats.
 */
export function buildDatasetSummaryQuery(): string {
  return (
    '{}\n' +
    `| select(${DATASET_SUMMARY_SELECT.join(', ')})\n` +
    `  by (${DATASET_SUMMARY_BY.join(', ')})`
  );
}

// ── Dataset Task Query ──
// Aggregates task-level stats for a specific dataset.

const DATASET_TASK_SELECT = [
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

const DATASET_TASK_BY = ['task_id'];

/**
 * Builds a TraceQL aggregation query for tasks within a specific dataset.
 * Filters by dataset_name and groups by task_id.
 */
export function buildDatasetTaskQuery(
  datasetName: string,
  filters?: { language?: string }
): string {
  const conditions: string[] = [`dataset_name="${datasetName}"`];
  if (filters?.language) conditions.push(`task_language="${filters.language}"`);
  const selector = `{${conditions.join(' and ')}}`;
  return (
    `${selector}\n` +
    `| select(${DATASET_TASK_SELECT.join(', ')})\n` +
    `  by (${DATASET_TASK_BY.join(', ')})`
  );
}
