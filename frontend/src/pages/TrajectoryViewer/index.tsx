import { useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';
import { Skeleton, Alert as AntAlert, Breadcrumb, Tag } from 'antd';
import {
  WarningOutlined,
  InfoCircleOutlined,
  ExclamationCircleOutlined,
  RightOutlined,
  DownOutlined,
} from '@ant-design/icons';
import MetricCard from '../../components/shared/MetricCard';
import OutcomeBadge from '../../components/shared/OutcomeBadge';
import { queryTraceQL } from '../../api/traceql';
import { buildTrajectoryDetailQuery } from '../../queries/trajectory';
import type { OutcomeType } from '../../types';
import styles from './styles.module.css';

// ── Trajectory type ──

interface TrajectoryItem {
  id: string;
  experiment_id: string;
  iteration: number;
  task_id: string;
  task_language: string;
  scaffold: string;
  outcome: 'success' | 'failure' | 'timeout' | 'error';
  reward: number;
  reward_components: Record<string, number>;
  total_turns: number;
  duration_ms: number;
  total_tokens: number;
  input_tokens: number;
  output_tokens: number;
  cache_tokens: number;
  model: string;
  run_code: string;
  run_duration_ms: number;
  sandbox_create_duration_ms: number;
  verify_duration_ms: number;
  trace_id: string;
  tool_schema: string;
}

// ── ATIF-v1.6 types ──

interface ATIFMetrics {
  prompt_tokens: number;
  completion_tokens: number;
  cached_tokens?: number;
}

interface ATIFToolCall {
  tool_call_id: string;
  function_name: string;
  arguments: Record<string, unknown>;
}

interface ATIFStep {
  step_id: number;
  timestamp: string;
  source: 'user' | 'agent';
  message: string;
  reasoning_content?: string;
  model_name?: string;
  tool_calls?: ATIFToolCall[];
  observation?: { results: { content: string }[] };
  metrics?: ATIFMetrics;
}

interface ATIFTrajectory {
  schema_version: string;
  session_id: string;
  agent: { name: string; version: string; model_name: string };
  steps: ATIFStep[];
  final_metrics?: {
    total_prompt_tokens: number;
    total_completion_tokens: number;
    total_cached_tokens: number;
  };
}

// ── Turn types ──

interface TurnData {
  id: string;
  turn_num: number;
  source: 'user' | 'agent';
  tool_names: string[];
  has_error: boolean;
  total_tokens: number;
  events: TurnEvent[];
}

type TurnEvent =
  | { id: string; type: 'message'; content: string }
  | {
      id: string;
      type: 'reasoning';
      content: string;
      model_name?: string;
      completion_tokens?: number;
    }
  | { id: string; type: 'action'; function_name: string; arguments: Record<string, unknown> }
  | { id: string; type: 'observation'; content: string; has_error: boolean };

interface AnnotationItem {
  id: string;
  description: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

// ── Helpers ──

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatTokens(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return `${n}`;
}

// ── Severity labels (colors via CSS module) ──

const SEVERITY_LABELS: Record<string, string> = {
  error: 'Error',
  critical: 'Critical',
  warning: 'Warning',
  info: 'Info',
};

function severityBadgeClass(sev: string): string {
  if (sev === 'error' || sev === 'critical') return styles.severityError;
  if (sev === 'warning') return styles.severityWarning;
  return styles.severityInfo;
}

// ── Pattern type labels ──

const PATTERN_LABELS: Record<string, string> = {
  action_loop: '🔄 Action Loop',
  tool_error: '🔧 Tool Error',
  timeout: '⏱ Timeout',
  token_explosion: '💥 Token Explosion',
  ineffective_action: '❌ Ineffective Action',
  early_abandon: '🏳 Early Abandon',
  repeat_error: '🔁 Repeat Error',
};

// ── Truncatable text ──

function TruncatableText({
  text,
  maxChars = 200,
  mono = false,
  color: textColor,
}: {
  text: string;
  maxChars?: number;
  mono?: boolean;
  color?: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const needsTruncation = text.length > maxChars;
  const displayText = expanded || !needsTruncation ? text : text.slice(0, maxChars) + '...';

  return (
    <div>
      <pre
        className={clsx(styles.truncatablePre, { 'font-mono': mono })}
        style={textColor ? { color: textColor } : undefined}
      >
        {displayText}
      </pre>
      {needsTruncation && (
        <button
          type="button"
          onClick={e => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
          className={styles.truncatableToggle}
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      )}
    </div>
  );
}

// ── Event component ──

function EventBlock({ event }: { event: TurnEvent }) {
  const [outputExpanded, setOutputExpanded] = useState(false);

  if (event.type === 'message') {
    return (
      <div className={styles.eventRowReasoning}>
        <span className={styles.eventEmoji}>📝</span>
        <div className={styles.eventMain}>
          <div className={styles.eventTitleRow}>
            <span className={styles.eventKind}>Analysis / Plan</span>
          </div>
          <TruncatableText text={event.content} maxChars={300} />
        </div>
      </div>
    );
  }

  if (event.type === 'reasoning') {
    const badge = [
      event.completion_tokens != null ? `${event.completion_tokens} tokens` : null,
      event.model_name,
    ]
      .filter(Boolean)
      .join(' · ');

    return (
      <div className={styles.eventRowReasoning}>
        <span className={styles.eventEmoji}>🧠</span>
        <div className={styles.eventMain}>
          <div className={styles.eventTitleRow}>
            <span className={styles.eventKind}>Reasoning</span>
            {badge && <span className={styles.monoMuted}>{badge}</span>}
          </div>
          <TruncatableText text={event.content || 'Thinking...'} maxChars={200} mono />
        </div>
      </div>
    );
  }

  if (event.type === 'action') {
    const inputText = JSON.stringify(event.arguments, null, 2);

    return (
      <div className={styles.eventRowAction}>
        <span className={styles.eventEmoji}>🔧</span>
        <div className={styles.eventMain}>
          <div className={styles.eventTitleRow}>
            <span className={styles.eventKind}>Action</span>
            <Tag className="!m-0">{event.function_name}</Tag>
          </div>
          {inputText && (
            <div className="mb-1">
              <div className={styles.fieldLabel}>Arguments:</div>
              <TruncatableText
                text={inputText}
                maxChars={200}
                mono
                color="var(--color-text-primary)"
              />
            </div>
          )}
        </div>
      </div>
    );
  }

  // observation
  return (
    <div
      className={clsx(styles.eventRowObservation, {
        [styles.eventRowActionError]: event.has_error,
      })}
    >
      <span className={styles.eventEmoji}>👁️</span>
      <div className={styles.eventMain}>
        <div className={styles.eventTitleRow}>
          <span className={styles.eventKind}>Observation</span>
          {event.has_error && (
            <span className={styles.statusPillErr}>
              <WarningOutlined /> Error
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={e => {
            e.stopPropagation();
            setOutputExpanded(!outputExpanded);
          }}
          className={styles.outputToggle}
        >
          {outputExpanded ? (
            <DownOutlined className={styles.miniIcon} />
          ) : (
            <RightOutlined className={styles.miniIcon} />
          )}
          Output ({event.content.length} chars)
        </button>
        {outputExpanded && (
          <TruncatableText
            text={event.content || '(empty)'}
            maxChars={500}
            mono
            color={event.has_error ? 'var(--color-error)' : 'var(--color-text-tertiary)'}
          />
        )}
      </div>
    </div>
  );
}

// ── Turn Card ──

function TurnCard({ turn, defaultOpen = false }: { turn: TurnData; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen || turn.has_error);

  return (
    <div
      className={clsx(styles.turnCard, {
        [styles.turnCardError]: turn.has_error,
      })}
    >
      {/* Header */}
      <div onClick={() => setOpen(!open)} className={styles.turnHeader}>
        <div className={styles.turnHeaderLeft}>
          <span className={styles.turnChevron}>{open ? <DownOutlined /> : <RightOutlined />}</span>
          <span className={clsx(styles.turnTitle, 'font-mono')}>Step #{turn.turn_num}</span>
          {turn.tool_names.map(name => (
            <Tag key={name} className="!m-0">
              {name}
            </Tag>
          ))}
          {turn.has_error && (
            <span className={styles.statusPillErr}>
              <WarningOutlined /> ERROR
            </span>
          )}
        </div>
        <div className={styles.turnHeaderRight}>
          <span className="font-mono">{formatTokens(turn.total_tokens)}t</span>
          <Tag className="!m-0" color={turn.source === 'agent' ? 'blue' : 'default'}>
            {turn.source}
          </Tag>
        </div>
      </div>

      {/* Content */}
      {open && (
        <div className={styles.turnContent}>
          {turn.events.map(ev => (
            <EventBlock key={ev.id} event={ev} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Annotation Section ──

function AnnotationSection({ annotations }: { annotations: AnnotationItem[] }) {
  if (annotations.length === 0) return null;

  const severityIcon = (sev: string) => {
    if (sev === 'error' || sev === 'critical')
      return <ExclamationCircleOutlined className="tone-error" />;
    if (sev === 'warning') return <WarningOutlined className="tone-warning" />;
    return <InfoCircleOutlined className="tone-info" />;
  };

  const severityBadge = (sev: string) => {
    const label = SEVERITY_LABELS[sev] ?? SEVERITY_LABELS.info;
    return <span className={severityBadgeClass(sev)}>{label}</span>;
  };

  return (
    <div className={styles.annotationBox}>
      <div className={styles.annotationHeader}>
        <WarningOutlined className={styles.annotationBannerIcon} />
        <span className={styles.annotationTitle}>Detected Issue Patterns</span>
      </div>
      {annotations.map(ann => (
        <div key={ann.id} className={styles.annotationRow}>
          <span className={styles.annotationIcon}>{severityIcon(ann.severity)}</span>
          <div className={styles.annotationBody}>
            <div className={styles.annotationMeta}>
              <span className={styles.turnRange}>
                {ann.affected_turns.length > 0 && (
                  <>
                    Turn #{ann.affected_turns[0]}
                    {ann.affected_turns.length > 1 &&
                      `–#${ann.affected_turns[ann.affected_turns.length - 1]}`}
                  </>
                )}
              </span>
              {ann.pattern_type && (
                <span className={styles.patternLabel}>
                  {PATTERN_LABELS[ann.pattern_type] ?? ann.pattern_type}
                </span>
              )}
              {severityBadge(ann.severity)}
            </div>
            <div className={styles.annotationDesc}>{ann.description}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Reward Components ──

function RewardComponentsBadges({ components }: { components: Record<string, number> }) {
  const entries = Object.entries(components);
  if (entries.length === 0) return null;

  return (
    <div className={styles.badgeRow}>
      {entries.map(([key, val]) => (
        <span
          key={key}
          className={
            val > 0
              ? styles.rewardBadgePos
              : val < 0
                ? styles.rewardBadgeNeg
                : styles.rewardBadgeNeutral
          }
        >
          {key}: {typeof val === 'number' ? val.toFixed(2) : val}
        </span>
      ))}
    </div>
  );
}

// ── Info tag helper ──

function InfoTag({ label, value }: { label: string; value: string }) {
  return (
    <span>
      <span className={styles.infoTagLabel}>{label}: </span>
      <span className={styles.infoTagValue}>{value}</span>
    </span>
  );
}

// ── Shared panel (used by full page and Drawer) ──

export function TrajectoryViewerPanel({ id }: { id: string }) {
  const {
    data: trajRows,
    isLoading: trajLoading,
    isError: trajError,
    error: trajQueryError,
  } = useQuery({
    queryKey: ['trajectory-detail', id],
    queryFn: () => queryTraceQL(buildTrajectoryDetailQuery(id)),
    enabled: !!id,
    staleTime: 30_000,
  });

  const trajectory = useMemo((): TrajectoryItem | null => {
    if (!trajRows || trajRows.length === 0) return null;
    const row = trajRows[0];
    return {
      id: String(row.id ?? ''),
      experiment_id: String(row.experiment_id ?? ''),
      iteration: (row.iteration as number) ?? 0,
      task_id: String(row.task_id ?? ''),
      task_language: String(row.task_language ?? ''),
      scaffold: String(row.scaffold ?? ''),
      outcome: (row.verify_code as TrajectoryItem['outcome']) ?? 'error',
      reward: (row.reward as number) ?? 0,
      reward_components: {},
      total_turns: (row.turns as number) ?? 0,
      duration_ms: (row.duration_ms as number) ?? 0,
      total_tokens: (row.total_tokens as number) ?? 0,
      input_tokens: (row.input_tokens as number) ?? 0,
      output_tokens: (row.output_tokens as number) ?? 0,
      cache_tokens: (row.cache_tokens as number) ?? 0,
      model: String(row.model ?? ''),
      run_code: String(row.run_code ?? ''),
      run_duration_ms: (row.run_duration_ms as number) ?? 0,
      sandbox_create_duration_ms: (row.sandbox_create_duration_ms as number) ?? 0,
      verify_duration_ms: (row.verify_duration_ms as number) ?? 0,
      trace_id: String(row.trace_id ?? ''),
      tool_schema: String(row.tool_schema ?? ''),
    };
  }, [trajRows]);

  const annotationsData = null;
  const annotations = useMemo(() => annotationsData?.items ?? [], [annotationsData]);

  const turns = useMemo((): TurnData[] => {
    if (!trajRows || trajRows.length === 0) return [];
    const raw = trajRows[0].trajectory;
    if (!raw) return [];

    let parsed: ATIFTrajectory;
    try {
      parsed = typeof raw === 'string' ? JSON.parse(raw) : (raw as ATIFTrajectory);
    } catch {
      return [];
    }

    return (parsed.steps ?? []).map((s): TurnData => {
      const obsContent = s.observation?.results?.map(r => r.content).join('\n') ?? '';
      const hasError =
        obsContent.includes('command not found') ||
        obsContent.includes('No such file') ||
        obsContent.includes('Error') ||
        obsContent.includes('error:') ||
        obsContent.includes('failed');

      const events: TurnEvent[] = [];

      if (s.message) {
        events.push({ id: `${s.step_id}-msg`, type: 'message', content: s.message });
      }
      if (s.reasoning_content) {
        events.push({
          id: `${s.step_id}-reasoning`,
          type: 'reasoning',
          content: s.reasoning_content,
          model_name: s.model_name,
          completion_tokens: s.metrics?.completion_tokens,
        });
      }
      for (const tc of s.tool_calls ?? []) {
        events.push({
          id: tc.tool_call_id,
          type: 'action',
          function_name: tc.function_name,
          arguments: tc.arguments,
        });
      }
      if (obsContent) {
        events.push({
          id: `${s.step_id}-obs`,
          type: 'observation',
          content: obsContent,
          has_error: hasError,
        });
      }

      return {
        id: `step-${s.step_id}`,
        turn_num: s.step_id,
        source: s.source,
        tool_names: (s.tool_calls ?? []).map(tc => tc.function_name),
        has_error: hasError,
        total_tokens: (s.metrics?.prompt_tokens ?? 0) + (s.metrics?.completion_tokens ?? 0),
        events,
      };
    });
  }, [trajRows]);

  if (trajLoading) {
    return <Skeleton active paragraph={{ rows: 8 }} />;
  }

  if (trajError || !trajectory) {
    const apiDetail =
      trajQueryError instanceof Error
        ? trajQueryError.message
        : trajQueryError
          ? String(trajQueryError)
          : null;
    const description = trajError
      ? apiDetail
        ? `Request failed: ${apiDetail}`
        : 'The trace query request failed (network or server error).'
      : `No row returned for this id from TraceQL — it may not exist in the current project/time range, or the backend uses a different id field.`;
    return (
      <AntAlert
        type="error"
        message="Failed to load trajectory"
        description={
          <>
            <div>
              <strong>{id}</strong>
            </div>
            <div style={{ marginTop: 8 }}>{description}</div>
          </>
        }
        showIcon
      />
    );
  }

  const t = trajectory;
  const rewardComponents = t.reward_components || {};
  const hasRewardComponents = Object.keys(rewardComponents).length > 0;

  const rewardTotalClass =
    t.reward > 0
      ? styles.rewardTotalPos
      : t.reward < 0
        ? styles.rewardTotalNeg
        : styles.rewardTotalNeutral;

  return (
    <>
      {/* A. Trajectory Info Card */}
      <div className={styles.infoCard}>
        <div className={styles.metaRow}>
          <InfoTag label="Experiment" value={t.experiment_id} />
          <InfoTag label="Iteration" value={`#${t.iteration}`} />
          <InfoTag label="Task" value={t.task_id} />
          <InfoTag label="Scaffold" value={t.scaffold} />
        </div>
        <div className={styles.metricsRow}>
          <MetricCard title="Reward" value={t.reward.toFixed(2)} />
          <div className={styles.outcomeCard}>
            <div className={styles.outcomeLabel}>OUTCOME</div>
            <OutcomeBadge outcome={t.outcome as OutcomeType} />
          </div>
          <MetricCard title="Turns" value={t.total_turns} />
          <MetricCard title="Tokens" value={formatTokens(t.total_tokens)} />
          <MetricCard title="Duration" value={formatDuration(t.duration_ms)} />
        </div>
        {hasRewardComponents && (
          <div className={styles.rewardBreakdown}>
            <span className={styles.rewardBreakdownLabel}>Reward Breakdown:</span>
            <span className={rewardTotalClass}>Total: {t.reward.toFixed(2)}</span>
            <RewardComponentsBadges components={rewardComponents} />
          </div>
        )}
      </div>

      {/* B. Annotations */}
      <AnnotationSection annotations={annotations} />

      {/* C. Turn Timeline */}
      <div className={styles.timelineHeading}>
        <h2 className={styles.timelineTitle}>
          Turn Timeline
          <span className={styles.timelineCount}>{turns.length} turns</span>
        </h2>
      </div>
      {turns.length === 0 ? (
        <div className={styles.emptyTurns}>No turns found</div>
      ) : (
        turns.map((turn: TurnData) => (
          <TurnCard key={turn.id} turn={turn} defaultOpen={turn.has_error} />
        ))
      )}
    </>
  );
}

// ── Full page ──

export default function TrajectoryViewer() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className={styles.page}>
      <Breadcrumb
        className={styles.breadcrumb}
        items={[
          { title: <Link to="/experiments">Experiments</Link> },
          { title: 'Trajectory Explorer' },
          { title: 'Trajectory Viewer' },
        ]}
      />
      <h1 className={styles.pageTitle}>📜 Trajectory Viewer</h1>
      <TrajectoryViewerPanel id={id!} />
    </div>
  );
}
