import { useState, useMemo, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { Skeleton, Alert as AntAlert, message } from 'antd';
import { CopyOutlined, LinkOutlined, DownOutlined, RightOutlined } from '@ant-design/icons';
import OutcomeBadge from '../../components/shared/OutcomeBadge';
import { useTrace } from '../../api/traces';
import type { SpanData, RLContext } from '../../api/traces';
import type { OutcomeType } from '../../types';
import styles from './styles.module.css';

// ── Helpers ──

function formatDuration(ms: number): string {
  if (ms < 1) return '<1ms';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

// ── Span tree node ──

interface SpanNode {
  span: SpanData;
  children: SpanNode[];
  depth: number;
}

function buildSpanTree(spans: SpanData[]): SpanNode[] {
  const byId = new Map<string, SpanNode>();
  const roots: SpanNode[] = [];

  // Create nodes
  for (const s of spans) {
    byId.set(s.span_id, { span: s, children: [], depth: 0 });
  }

  // Link parent-child
  for (const s of spans) {
    const node = byId.get(s.span_id)!;
    if (s.parent_span_id && byId.has(s.parent_span_id)) {
      const parent = byId.get(s.parent_span_id)!;
      parent.children.push(node);
    } else {
      roots.push(node);
    }
  }

  // Set depths
  function setDepth(node: SpanNode, d: number) {
    node.depth = d;
    for (const c of node.children) setDepth(c, d + 1);
  }
  for (const r of roots) setDepth(r, 0);

  return roots;
}

function flattenTree(nodes: SpanNode[], collapsed: Set<string>): SpanNode[] {
  const result: SpanNode[] = [];
  function walk(ns: SpanNode[]) {
    for (const n of ns) {
      result.push(n);
      if (!collapsed.has(n.span.span_id)) {
        walk(n.children);
      }
    }
  }
  walk(nodes);
  return result;
}

// ── RL Context Card ──

function RLContextCard({ ctx }: { ctx: RLContext }) {
  const navigate = useNavigate();

  return (
    <div className={styles.panelPadded}>
      <div className={styles.rlContextHeader}>
        <span className={styles.rlContextEmoji}>📎</span>
        <span className={styles.rlContextTitle}>RL Context</span>
      </div>
      <div className={styles.rlContextGrid}>
        <CtxField label="Experiment" value={ctx.experiment_name} />
        <CtxField label="Trajectory" value={ctx.trajectory_id} mono />
        <CtxField label="Iteration" value={`#${ctx.iteration_num}`} />
        <CtxField label="Reward" value={ctx.reward.toFixed(2)} />
        <CtxField label="Turn" value={`#${ctx.turn_num}`} />
        <CtxField label="Task" value={ctx.task_id} mono />
      </div>
      <div className={styles.linkOutlineBtnMargin}>
        <button
          type="button"
          onClick={() => navigate(`/trajectories/${ctx.trajectory_id}`)}
          className={styles.linkOutlineBtn}
        >
          <LinkOutlined /> View Trajectory →
        </button>
      </div>
    </div>
  );
}

function CtxField({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <span className={styles.ctxLabel}>{label}: </span>
      <span className={clsx(styles.ctxValue, { 'font-mono': mono })}>{value}</span>
    </div>
  );
}

// ── Span Row ──

function SpanRow({
  node,
  selected,
  onClick,
  onToggle,
  collapsed,
  traceStart,
  traceDuration,
}: {
  node: SpanNode;
  selected: boolean;
  onClick: () => void;
  onToggle: () => void;
  collapsed: boolean;
  traceStart: number;
  traceDuration: number;
}) {
  const [hovered, setHovered] = useState(false);
  const s = node.span;
  const isError = s.status === 'error';
  const hasChildren = node.children.length > 0;

  // Compute waterfall bar position
  const spanStart = new Date(s.start_time).getTime();
  const offset = spanStart - traceStart;
  const leftPct = traceDuration > 0 ? (offset / traceDuration) * 100 : 0;
  const widthPct = traceDuration > 0 ? (s.duration_ms / traceDuration) * 100 : 100;

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={clsx(styles.spanRow, {
        [styles.spanRowHover]: hovered,
        [styles.spanRowSelected]: selected,
      })}
    >
      {/* Left: Name area (40%) */}
      <div className={styles.spanNameCol} style={{ paddingLeft: node.depth * 20 + 8 }}>
        {/* Toggle icon */}
        <span
          onClick={e => {
            e.stopPropagation();
            if (hasChildren) onToggle();
          }}
          className={clsx(styles.toggleCell, {
            'cursor-pointer': hasChildren,
            'cursor-default': !hasChildren,
          })}
        >
          {hasChildren ? (
            collapsed ? (
              <RightOutlined />
            ) : (
              <DownOutlined />
            )
          ) : (
            <span className={styles.dotBullet}>●</span>
          )}
        </span>
        {/* Span name */}
        <span
          className={clsx(styles.spanNameText, {
            [styles.spanNameTextError]: isError,
          })}
        >
          {s.operation_name}
        </span>
        {isError && <span className={styles.errorEmoji}>❌</span>}
      </div>

      {/* Right: Waterfall bar (60%) */}
      <div className={styles.waterfallTrack}>
        <div
          className={clsx(styles.waterfallBar, {
            'bg-tone-error': isError,
            'bg-tone-info': !isError,
          })}
          style={{
            left: `${Math.max(0, leftPct)}%`,
            width: `${Math.max(0.5, widthPct)}%`,
          }}
        />
        <span
          className={styles.durationLabel}
          style={{
            left: `${Math.min(95, Math.max(0, leftPct) + Math.max(0.5, widthPct) + 1)}%`,
          }}
        >
          {formatDuration(s.duration_ms)}
        </span>
      </div>
    </div>
  );
}

// ── Span Detail Panel ──

function SpanDetailPanel({ span }: { span: SpanData | null }) {
  if (!span) {
    return <div className={styles.detailEmpty}>Click a span to view details</div>;
  }

  const isError = span.status === 'error';
  const errorAttr = span.attributes.find(a => a.key === 'error.message' || a.key === 'error');

  return (
    <div className={styles.detailBody}>
      {/* Span header */}
      <div className={styles.detailHeaderBlock}>
        <div className={styles.detailOpTitle}>{span.operation_name}</div>
        <div className={styles.detailMetaRow}>
          <span>Duration: {formatDuration(span.duration_ms)}</span>
          <span>
            Status:{' '}
            <span className={isError ? styles.statusErr : styles.statusOk}>
              {span.status.toUpperCase()}
            </span>
          </span>
        </div>
      </div>

      {/* Error highlight */}
      {isError && errorAttr && <div className={styles.errorBox}>{errorAttr.value}</div>}

      {/* Attributes table */}
      <div>
        <div className={styles.sectionLabel}>Attributes</div>
        <table className={styles.attrTable}>
          <tbody>
            {span.attributes.map((attr, i) => (
              <tr key={i} className={styles.attrRow}>
                <td className={styles.attrKeyCell}>{attr.key}</td>
                <td
                  className={clsx(styles.attrValueCell, {
                    [styles.attrValueCellError]:
                      attr.key === 'error' || attr.key === 'error.message',
                  })}
                >
                  {attr.value}
                </td>
              </tr>
            ))}
            {span.attributes.length === 0 && (
              <tr>
                <td colSpan={2} className={styles.attrEmptyCell}>
                  No attributes
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Events */}
      {span.events.length > 0 && (
        <div className={styles.eventsSection}>
          <div className={styles.sectionLabel}>Events</div>
          {span.events.map((ev, i) => (
            <div key={i} className={styles.eventCard}>
              <span className={styles.eventName}>{ev.name}</span>
              {ev.attributes &&
                Object.entries(ev.attributes).map(([k, v]) => (
                  <div key={k} className={styles.eventAttrLine}>
                    {k}: {String(v)}
                  </div>
                ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Time Axis ──

function TimeAxis({ durationMs, tickCount = 5 }: { durationMs: number; tickCount?: number }) {
  const ticks = [];
  for (let i = 0; i <= tickCount; i++) {
    const val = (durationMs / tickCount) * i;
    ticks.push({
      label: formatDuration(val),
      pct: (i / tickCount) * 100,
    });
  }

  return (
    <div className={styles.timeAxis}>
      {ticks.map((t, i) => (
        <span
          key={i}
          className={clsx(styles.timeAxisTick, {
            [styles.timeAxisTickEnd]: i === ticks.length - 1,
          })}
          style={{ left: `${t.pct}%` }}
        >
          {t.label}
        </span>
      ))}
    </div>
  );
}

// ── Main Page ──

export default function TraceViewer() {
  const { traceId } = useParams<{ traceId: string }>();
  const { data, isLoading, isError } = useTrace(traceId);
  const [selectedSpanId, setSelectedSpanId] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  const trace = data?.trace;
  const rlContext = data?.rl_context ?? null;

  const spanTree = useMemo(() => (trace?.spans ? buildSpanTree(trace.spans) : []), [trace]);

  const flatSpans = useMemo(() => flattenTree(spanTree, collapsed), [spanTree, collapsed]);

  const selectedSpan = useMemo(() => {
    if (!selectedSpanId || !trace?.spans) return null;
    return trace.spans.find(s => s.span_id === selectedSpanId) ?? null;
  }, [selectedSpanId, trace]);

  const traceStart = useMemo(() => {
    if (!trace?.spans?.length) return 0;
    return Math.min(...trace.spans.map(s => new Date(s.start_time).getTime()));
  }, [trace]);

  const traceDuration = trace?.duration_ms ?? 0;

  const toggleCollapse = useCallback((spanId: string) => {
    setCollapsed(prev => {
      const next = new Set(prev);
      if (next.has(spanId)) next.delete(spanId);
      else next.add(spanId);
      return next;
    });
  }, []);

  const handleCopy = useCallback(() => {
    if (traceId) {
      navigator.clipboard.writeText(traceId).then(() => {
        message.success('Trace ID copied');
      });
    }
  }, [traceId]);

  if (isLoading) {
    return (
      <div className={styles.pagePad}>
        <Skeleton active paragraph={{ rows: 10 }} />
      </div>
    );
  }

  if (isError || !trace) {
    return (
      <div className={styles.pagePad}>
        <AntAlert
          type="error"
          message="Failed to load trace"
          description={`Trace ${traceId} not found or API error.`}
          showIcon
        />
      </div>
    );
  }

  const statusOutcome: OutcomeType = trace.has_error ? 'failure' : 'success';

  return (
    <div className={styles.page}>
      {/* A. RL Context Card */}
      {rlContext && <RLContextCard ctx={rlContext} />}

      {/* B. Trace Header */}
      <div className={styles.traceHeader}>
        <div className="flex items-center gap-2">
          <span className={styles.traceIdLabel}>Trace ID:</span>
          <span className={styles.traceIdValue}>{traceId}</span>
          <CopyOutlined onClick={handleCopy} className={styles.copyIcon} />
        </div>
        <div className={styles.metaMuted}>Duration: {formatDuration(traceDuration)}</div>
        <div className={styles.metaMuted}>Spans: {trace.span_count}</div>
        <OutcomeBadge outcome={statusOutcome} />
      </div>

      {/* C. Span Waterfall */}
      <div className={styles.waterfallShell}>
        {/* Left: Waterfall (60%) */}
        <div className={styles.waterfallLeft}>
          <div className={styles.waterfallScroll}>
            {flatSpans.map(node => (
              <SpanRow
                key={node.span.span_id}
                node={node}
                selected={selectedSpanId === node.span.span_id}
                onClick={() => setSelectedSpanId(node.span.span_id)}
                onToggle={() => toggleCollapse(node.span.span_id)}
                collapsed={collapsed.has(node.span.span_id)}
                traceStart={traceStart}
                traceDuration={traceDuration}
              />
            ))}
          </div>
          {/* Time axis */}
          <TimeAxis durationMs={traceDuration} />
        </div>

        {/* Right: Detail Panel (40%) */}
        <div className={styles.detailPane}>
          <SpanDetailPanel span={selectedSpan} />
        </div>
      </div>
    </div>
  );
}
