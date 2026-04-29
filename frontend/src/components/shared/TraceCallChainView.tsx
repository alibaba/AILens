import { useMemo, useState } from 'react';
import clsx from 'clsx';
import { Tree, Tag } from 'antd';
import type { Trace, Span } from '../../api/traces';
import styles from './TraceCallChainView.module.css';

interface TraceCallChainViewProps {
  trace: Trace;
}

export default function TraceCallChainView({ trace }: TraceCallChainViewProps) {
  const [selectedSpan, setSelectedSpan] = useState<Span | null>(null);

  const treeData = useMemo(() => {
    return buildTreeData(trace.spans);
  }, [trace.spans]);

  const timeRange = useMemo(() => {
    if (trace.spans.length === 0) return { start: 0, end: 0 };
    const starts = trace.spans.map(s => s.start_time);
    const ends = trace.spans.map(s => s.start_time + s.duration_ms);
    return {
      start: Math.min(...starts),
      end: Math.max(...ends),
    };
  }, [trace.spans]);

  return (
    <div className={styles.layout}>
      <div className={styles.treePane}>
        <Tree
          treeData={treeData}
          defaultExpandAll
          showLine
          onSelect={(keys, info) => {
            const span = (info.node as { span?: Span }).span;
            if (span) setSelectedSpan(span);
          }}
        />
      </div>

      <div className={styles.detailPane}>
        {selectedSpan ? (
          <SpanDetail span={selectedSpan} timeRange={timeRange} />
        ) : (
          <div className={styles.emptyHint}>Click a span to view details</div>
        )}
      </div>
    </div>
  );
}

function buildTreeData(spans: Span[]) {
  const byId = new Map<string, { span: Span; children: Span[] }>();
  const roots: Span[] = [];

  for (const span of spans) {
    byId.set(span.span_id, { span, children: [] });
  }

  for (const span of spans) {
    if (span.parent_span_id && byId.has(span.parent_span_id)) {
      byId.get(span.parent_span_id)!.children.push(span);
    } else {
      roots.push(span);
    }
  }

  function toTreeNode(span: Span): object {
    const node = byId.get(span.span_id)!;
    const isError = span.status === 'error';

    return {
      key: span.span_id,
      title: (
        <span className={styles.treeTitleRow}>
          <span className={clsx(styles.opName, { [styles.opNameError]: isError })}>
            {span.operation_name}
          </span>
          <Tag className={styles.tagTight}>{span.service_name}</Tag>
          <span className={styles.durationLabel}>{formatDuration(span.duration_ms)}</span>
          {isError && <span className={styles.errorMark}>❌</span>}
        </span>
      ),
      span,
      children: node.children.length > 0 ? node.children.map(toTreeNode) : undefined,
    };
  }

  return roots.map(toTreeNode);
}

function SpanDetail({
  span,
  timeRange,
}: {
  span: Span;
  timeRange: { start: number; end: number };
}) {
  const isError = span.status === 'error';
  const durationPct =
    timeRange.end > timeRange.start
      ? ((span.duration_ms / (timeRange.end - timeRange.start)) * 100).toFixed(2)
      : '0';

  const barLeft =
    timeRange.end > timeRange.start
      ? `${((span.start_time - timeRange.start) / (timeRange.end - timeRange.start)) * 100}%`
      : '0%';
  const barWidth = `${Math.max(1, parseFloat(durationPct))}%`;

  return (
    <div>
      <div className={styles.detailHeader}>
        <div className={styles.detailOpName}>{span.operation_name}</div>
        <div className={styles.detailService}>{span.service_name}</div>
      </div>

      <div className={styles.metricsGrid}>
        <div className={styles.metricBox}>
          <div className={styles.metricLabel}>Duration</div>
          <div className={styles.metricValueMono}>{formatDuration(span.duration_ms)}</div>
        </div>
        <div className={styles.metricBox}>
          <div className={styles.metricLabel}>Status</div>
          <div className={isError ? styles.statusErr : styles.statusOk}>
            {span.status.toUpperCase()}
          </div>
        </div>
      </div>

      <div className={styles.timelineBlock}>
        <div className={styles.timelineLabel}>Timeline</div>
        <div className={styles.timelineTrack}>
          <div
            className={clsx(styles.timelineBar, {
              [styles.timelineBarErr]: isError,
              [styles.timelineBarOk]: !isError,
            })}
            style={{ left: barLeft, width: barWidth }}
          />
        </div>
      </div>

      {span.attributes.length > 0 && (
        <div>
          <div className={styles.attrSectionLabel}>Attributes</div>
          <table className={styles.attrTable}>
            <tbody>
              {span.attributes.map((attr, i) => (
                <tr key={i}>
                  <td className={styles.attrKey}>{attr.key}</td>
                  <td className={styles.attrVal}>{attr.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {isError && span.status_message && (
        <div className={styles.errorBox}>{span.status_message}</div>
      )}
    </div>
  );
}

function formatDuration(ms: number): string {
  if (ms < 1) return '<1ms';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}
