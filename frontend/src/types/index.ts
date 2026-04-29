// ── Core domain types — aligned with backend API schema ──

export interface TimeSeriesPoint {
  time: number; // unix timestamp（timestamp 模式用）
  iteration: number; // 迭代编号（iteration 模式用）
  value: number;
  labels: Record<string, string>;
}

export interface TimeSeries {
  name: string;
  labels: Record<string, string>;
  points: TimeSeriesPoint[];
  xAxisType: 'iteration' | 'timestamp';
}

// ── Tab 2: Task Analysis ──

export type TaskClassification = 'all_pass' | 'all_fail' | 'mixed' | 'unverified';

export interface TaskEffectivenessSummary {
  all_pass: number;
  all_fail: number;
  mixed: number;
  unverified: number;
  total: number;
}

export interface TaskEffectivenessItem {
  task_id: string;
  language: string;
  scaffold: string;
  tool_schema: string;
  dataset_name: string;
  rollout_count: number;
  valid_count: number;
  pass_count: number;
  fail_count: number;
  pass_rate: number;
  first_pass_iteration: number | null;
  classification: TaskClassification;
}

export interface TaskEffectivenessResponse {
  summary: TaskEffectivenessSummary;
  tasks: TaskEffectivenessItem[];
}

// ── Task Library (global view across all experiments) ──

export interface TaskLibraryItem {
  task_id: string;
  task_language: string;
  experiment_count: number;
  trajectory_count: number;
  pass_count: number;
  fail_count: number;
  pass_rate: number;
  max_turns: number;
  min_turns: number;
  avg_turns: number;
  max_duration_ms: number;
  min_duration_ms: number;
  avg_duration_ms: number;
}

export interface TaskExperimentItem {
  task_id: string;
  experiment_id: string;
  task_language: string;
  rollout_count: number;
  pass_count: number;
  fail_count: number;
  pass_rate: number;
  avg_reward: number;
  avg_turns: number;
  avg_duration_ms: number;
}

export interface LanguageStatsItem {
  language: string;
  count: number;
  pass_rate: number;
  max_turns_passed: number;
  avg_turns_passed: number;
  max_duration_passed_ms: number;
  avg_duration_passed_ms: number;
}

export interface LanguageStatsResponse {
  items: LanguageStatsItem[];
}

// ── Tab 3: Behavior Analysis ──

export interface ToolQualityItem {
  tool: string;
  scaffold: string;
  call_count: number;
  success_rate: number;
  error_task_pct: number;
  success_task_pct: number;
  trajectory_count: number;
  // TASK-036: task dimension rates
  at_least_one_error_task_rate: number;
  at_least_one_success_task_rate: number;
}

export interface ToolQualityResponse {
  items: ToolQualityItem[];
}

export interface ToolLatencyItem {
  tool: string;
  call_count: number;
  avg_ms: number;
  p50_ms: number;
  p99_ms: number;
}

export interface ToolLatencyResponse {
  items: ToolLatencyItem[];
}

export interface ScaffoldStatsItem {
  scaffold: string;
  count: number;
  pass_rate: number;
  max_turns_passed: number;
  avg_turns_passed: number;
  max_duration_passed_ms: number;
  avg_duration_passed_ms: number;
}

export interface ScaffoldStatsResponse {
  items: ScaffoldStatsItem[];
}

// NOTE: TurnStatsResponse and TurnBucket removed - Turn Analysis now uses PromQL metrics

export type OutcomeType = 'success' | 'failure' | 'timeout' | 'error' | 'running';

export type ExperimentStatus =
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'paused'
  | 'unknown';

// ── Project ──

export interface Project {
  id: string;
  name: string;
  description: string;
  owner: string;
  tags: Record<string, string>;
}

export interface ProjectsResponse {
  total: number;
  items: Project[];
  page: number;
  page_size: number;
}

// ── Experiment ──

export interface ExperimentConfig {
  model: string;
  scaffolds: string[];
  algorithm: string;
  reward_function: string;
  reward_components: string[];
}

export interface ExperimentItem {
  id: string;
  project_id: string;
  name: string;
  status: ExperimentStatus;
  config: ExperimentConfig;
  tags: Record<string, string>;
  created_at: string;
  updated_at: string;
  latest_iteration: number;
  mean_reward: number;
  pass_rate: number;
  total_trajectories: number;
  total_tokens: number;
}

export interface ExperimentsResponse {
  total: number;
  page: number;
  page_size: number;
  items: ExperimentItem[];
}

// ── Trajectory (kept for other pages) ──

export interface Trajectory {
  id: string;
  iterationId: string;
  experimentId: string;
  outcome: OutcomeType;
  totalReward: number;
  turnCount: number;
  durationMs: number;
  startedAt: string;
  completedAt: string | null;
  metadata: Record<string, unknown>;
}

// ── Trace ──

export interface Trace {
  traceId: string;
  rootSpanId: string;
  serviceName: string;
  operationName: string;
  startTime: string;
  durationMs: number;
  spanCount: number;
  status: 'ok' | 'error';
  tags: Record<string, string>;
}

export interface Span {
  spanId: string;
  traceId: string;
  parentSpanId: string | null;
  operationName: string;
  serviceName: string;
  startTime: string;
  durationMs: number;
  status: 'ok' | 'error';
  tags: Record<string, string>;
  logs: SpanLog[];
}

export interface SpanLog {
  timestamp: string;
  fields: Record<string, string>;
}

// ── Alert ──

export interface Alert {
  id: string;
  name: string;
  severity: 'critical' | 'warning' | 'info';
  status: 'firing' | 'resolved' | 'silenced';
  source: string;
  message: string;
  firedAt: string;
  resolvedAt: string | null;
  labels: Record<string, string>;
}

// ── Iteration list ──

export interface IterationItem {
  id: string;
  experiment_id: string;
  iteration_num: number;
  timestamp: string;
  checkpoint: string;
  metrics: Record<string, number>;
}

export interface IterationsResponse {
  items: IterationItem[];
}

// ── Annotation ──

export interface Annotation {
  id: string;
  targetType: 'trajectory' | 'turn' | 'span';
  targetId: string;
  author: string;
  content: string;
  rating: number | null;
  createdAt: string;
}

// ── M3: Pass Rate Diff ──

export interface PassRateDiffSummary {
  improved: number;
  unchanged: number;
  degraded: number;
}

export interface PassRateDiffItem {
  task_id: string;
  language: string;
  category: string;
  pass_rate_a: number;
  pass_rate_b: number;
  change: number;
  change_group: 'improved' | 'unchanged' | 'degraded';
}

export interface PassRateDiffResponse {
  step_a: number;
  step_b: number;
  total_tasks: number;
  summary: PassRateDiffSummary;
  items: PassRateDiffItem[];
}

// ── M3: Cross Analysis ──

export interface CrossAnalysisCellData {
  improved: number;
  unchanged: number;
  degraded: number;
}

export interface CrossAnalysisResponse {
  row_dimension: string;
  col_dimension: string;
  rows: string[];
  cols: string[];
  cells: Record<string, Record<string, CrossAnalysisCellData>>;
}

// ── M4: Extreme Cases ──

export interface ExtremeCaseItem {
  task_id: string;
  language: string;
  category: string;
  pass_rate_a: number;
  pass_rate_b: number;
  change: number;
}

export interface ExtremeCasesResponse {
  threshold: number;
  extreme_improved: ExtremeCaseItem[];
  extreme_degraded: ExtremeCaseItem[];
  total_extreme: number;
}

// ── M4: Repetition Detection ──

export interface RepetitionStats {
  affected_trajectories: number;
  affected_rate: number;
  total_repeats: number;
  mean_repeats_per_affected: number;
}

export interface RepetitionDetectionResponse {
  total_trajectories: number;
  tool_call_repetition: RepetitionStats;
  response_repetition: RepetitionStats;
}
