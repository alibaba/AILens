// src/queries/experiment.ts

interface MetricDef {
  selects: string[];
  extraFilter?: string;
  extraGroupBy?: string[];
}

export const EXPERIMENT_METRIC_DEFS: Record<string, MetricDef> = {
  reward_stats: {
    selects: [
      'round(avg(reward), 4) as mean_reward',
      'stddev(reward) as reward_std',
      'count() as trajectory_count',
    ],
  },
  pass_rate: {
    selects: [
      "round(avg(if(verify_code='success', 1, 0)), 4) as pass_rate",
      'count() as trajectory_count',
    ],
  },
  token_stats: {
    selects: [
      'sum(input_tokens) as input_tokens',
      'sum(output_tokens) as output_tokens',
      'round(avg(total_tokens), 2) as tokens_per_traj',
      'count() as trajectory_count',
    ],
  },
  tokens_per_reward: {
    selects: [
      'round(avg(if(reward > 0, total_tokens / reward, 0)), 0) as tokens_per_reward',
      'count() as trajectory_count',
    ],
  },
  io_tokens_ratio: {
    selects: [
      'round(avg(if(output_tokens > 0, input_tokens / output_tokens, 0)), 4) as io_ratio',
      'count() as trajectory_count',
    ],
  },
  success_turns_stats: {
    extraFilter: 'verify_code="success"',
    selects: [
      'round(avg(turns), 2) as mean_turns',
      'min(turns) as min_turns',
      'max(turns) as max_turns',
      'count() as passed_count',
    ],
  },
  duration_stats: {
    selects: [
      'round(avg(duration_ms), 0) as total_duration_ms',
      'round(avg(sandbox_create_duration_ms), 0) as sandbox_duration_ms',
      'round(avg(verify_duration_ms), 0) as verify_duration_ms',
      'count() as trajectory_count',
    ],
  },
  trajectory_count: {
    selects: ['count() as trajectory_count'],
  },
  scaffold_stats: {
    selects: [
      'count() as trajectory_count',
      "round(avg(if(verify_code='success', 1, 0)), 4) as pass_rate",
      'round(avg(reward), 4) as mean_reward',
      'round(avg(turns), 2) as mean_turns',
      'round(avg(total_tokens), 2) as tokens_per_traj',
      'round(avg(duration_ms), 0) as total_duration_ms',
    ],
  },
  language_stats: {
    selects: [
      'count() as trajectory_count',
      "round(avg(if(verify_code='success', 1, 0)), 4) as pass_rate",
      "max(if(verify_code='success', turns, 0)) as max_turns_passed",
      "sum(if(verify_code='success', turns, 0)) as sum_turns_passed",
      "max(if(verify_code='success', duration_ms, 0)) as max_duration_passed_ms",
      "sum(if(verify_code='success', duration_ms, 0)) as sum_duration_passed_ms",
      "sum(if(verify_code='success', 1, 0)) as passed_count",
    ],
  },
  mean_turns: {
    selects: ['round(avg(turns), 2) as mean_turns', 'count() as trajectory_count'],
  },
  turns_distribution: {
    extraGroupBy: ['turns'],
    selects: [
      'count() as total_count',
      "sum(if(verify_code='success', 1, 0)) as passed_count",
      "max(if(verify_code='success', duration_ms, 0)) as max_duration_ms",
      "sum(if(verify_code='success', duration_ms, 0)) as sum_duration_ms",
    ],
  },
  task_turns: {
    extraGroupBy: ['task_id', 'task_language'],
    selects: ['round(avg(turns), 2) as mean_turns', 'count() as trajectory_count'],
  },
  task_effectiveness: {
    extraGroupBy: ['task_id', 'task_language', 'dataset_name'],
    selects: [
      'count() as rollout_count',
      "sum(if(verify_code='success' or verify_code='failure', 1, 0)) as valid_count",
      "sum(if(verify_code='success', 1, 0)) as pass_count",
      "round(avg(if(verify_code='success', 1, 0)), 4) as pass_rate",
      "min(if(verify_code='success', iteration, 0)) as first_pass_iteration",
    ],
  },
  // ── Quality Assessment ────────────────────────────────────────────────────
  tool_calls_repeat_dist: {
    extraGroupBy: ['turn_tool_calls_repeat_cnt'],
    selects: ['count() as count'],
  },
  tool_calls_oscillate_dist: {
    extraGroupBy: ['turn_tool_calls_oscillate_cnt'],
    selects: ['count() as count'],
  },
  message_quality_binary: {
    selects: [
      'sum(if(turn_message_looping_cnt > 0, 1, 0)) as has_looping',
      'sum(if(turn_message_gibberish_cnt > 0, 1, 0)) as has_gibberish',
      'count() as trajectory_count',
    ],
  },
};

export interface SelectQueryParams {
  /** Dimension values placed into the selector {k="v", ...}. Undefined/null/empty are omitted. */
  filters?: Record<string, string | number | undefined | null>;
  /** Dimensions to split by — added to by(...) and selected as dimension fields. */
  splitBy?: string[];
  /**
   * When true, iteration is excluded from the by(...) clause and select fields.
   * Use when querying across all iterations (no per-iteration breakdown needed).
   */
  omitIterationGroupBy?: boolean;
}

export function buildExperimentQuery(
  metricKey: string,
  experimentId: string,
  params?: SelectQueryParams
): string {
  const { filters = {}, splitBy = [], omitIterationGroupBy = false } = params ?? {};
  const def = EXPERIMENT_METRIC_DEFS[metricKey];
  if (!def) throw new Error(`Unknown metric key: ${metricKey}`);

  const selectorParts: string[] = [];
  if (experimentId) selectorParts.push(`experiment_id="${experimentId}"`);
  for (const [k, v] of Object.entries(filters)) {
    if (v === undefined || v === null) continue;
    if (typeof v === 'string' && v === '') continue;
    selectorParts.push(`${k}="${v}"`);
  }
  if (def.extraFilter) selectorParts.push(def.extraFilter);

  const byFields = [
    ...(omitIterationGroupBy ? [] : ['iteration']),
    ...splitBy,
    ...(def.extraGroupBy ?? []),
  ];

  if (byFields.length === 0) {
    throw new Error(
      `buildExperimentQuery: "${metricKey}" with omitIterationGroupBy=true produces an empty group-by clause. Provide splitBy or use a metric that has extraGroupBy.`
    );
  }

  const selectFields = [...byFields, ...def.selects];

  return (
    `{${selectorParts.join(' and ')}}\n` +
    `| select(${selectFields.join(', ')})\n` +
    `  by (${byFields.join(', ')})`
  );
}
