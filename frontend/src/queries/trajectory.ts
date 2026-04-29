// src/queries/trajectory.ts

const TRAJECTORY_FIELDS = [
  'id',
  'experiment_id',
  'iteration',
  'task_id',
  'task_language',
  'scaffold',
  'verify_code',
  'reward',
  'turns',
  'duration_ms',
  'total_tokens',
  'input_tokens',
  'output_tokens',
  'cache_tokens',
  'model',
  'run_code',
  'run_duration_ms',
  'sandbox_create_duration_ms',
  'verify_duration_ms',
  'trace_id',
  'tool_schema',
  'trajectory',
].join(', ');

export function buildTrajectoryDetailQuery(id: string): string {
  return `{id="${id}"} | select(${TRAJECTORY_FIELDS})`;
}

export function buildTrajectoryListQuery(
  experimentId: string | undefined,
  filters: {
    outcome?: string[];
    scaffold?: string;
    tool_schema?: string;
    iteration?: number;
    language?: string;
    reward_min?: number;
    reward_max?: number;
    task_id?: string;
    dataset_name?: string;
  }
): string {
  const conditions: string[] = [];
  if (experimentId) conditions.push(`experiment_id="${experimentId}"`);
  if (filters.dataset_name) conditions.push(`dataset_name="${filters.dataset_name}"`);
  if (filters.task_id !== undefined && filters.task_id !== '') {
    conditions.push(`task_id="${filters.task_id}"`);
  }
  if (filters.scaffold !== undefined && filters.scaffold !== '') {
    conditions.push(`scaffold="${filters.scaffold}"`);
  }
  if (filters.tool_schema !== undefined && filters.tool_schema !== '') {
    conditions.push(`tool_schema="${filters.tool_schema}"`);
  }
  if (filters.language !== undefined && filters.language !== '') {
    conditions.push(`task_language="${filters.language}"`);
  }
  if (filters.iteration !== undefined) {
    conditions.push(`iteration=${filters.iteration}`);
  }
  const outcome = filters.outcome;
  if (outcome !== undefined) {
    if (outcome.length === 1) {
      conditions.push(`verify_code="${outcome[0]}"`);
    } else if (outcome.length > 1) {
      const or = outcome.map(o => `verify_code="${o}"`).join(' or ');
      conditions.push(`(${or})`);
    }
  }
  if (filters.reward_min !== undefined) conditions.push(`reward>=${filters.reward_min}`);
  if (filters.reward_max !== undefined) conditions.push(`reward<=${filters.reward_max}`);
  return `{${conditions.join(' and ')}}`;
}

export function buildOutcomeStatsQuery(
  experimentId?: string,
  taskId?: string,
  datasetName?: string,
  iteration?: number,
  outcome?: string[],
  language?: string
): string {
  const conditions: string[] = [];
  if (experimentId) conditions.push(`experiment_id="${experimentId}"`);
  if (datasetName) conditions.push(`dataset_name="${datasetName}"`);
  if (taskId !== undefined && taskId !== '') conditions.push(`task_id="${taskId}"`);
  if (iteration !== undefined) conditions.push(`iteration=${iteration}`);
  if (language !== undefined && language !== '') conditions.push(`task_language="${language}"`);
  if (outcome && outcome.length === 1) {
    conditions.push(`verify_code="${outcome[0]}"`);
  } else if (outcome && outcome.length > 1) {
    const or = outcome.map(o => `verify_code="${o}"`).join(' or ');
    conditions.push(`(${or})`);
  }
  return `{${conditions.join(' and ')}} | select(verify_code, count() as trajectory_count) by (verify_code)`;
}
