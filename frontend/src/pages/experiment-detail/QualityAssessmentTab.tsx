// Quality Assessment Tab — repetition / looping / gibberish pie charts

import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import ChartPanel from '../../components/shared/ChartPanel';
import { useTraceQL } from '../../hooks/useTraceQL';
import { colors } from '../../styles/theme';

// ── Semantic colors ───────────────────────────────────────────────────────────

const COLOR_NO_ISSUE = '#22C55E';
const COLOR_ISSUE_1 = '#FACC15';
const COLOR_ISSUE_2 = '#F97316';
const COLOR_ISSUE_HIGH = '#EF4444';
const COLOR_HAS_ISSUE = '#EF4444';
const COLOR_NO_ISSUE_BINARY = '#3B82F6';

function countColor(cnt: number): string {
  if (cnt === 0) return COLOR_NO_ISSUE;
  if (cnt === 1) return COLOR_ISSUE_1;
  if (cnt <= 3) return COLOR_ISSUE_2;
  return COLOR_ISSUE_HIGH;
}

// ── Chart helpers ─────────────────────────────────────────────────────────────

interface PieSlice {
  value: number;
  name: string;
  itemStyle: { color: string };
}

function makePieOption(data: PieSlice[]): EChartsOption {
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: colors.panelBg,
      borderColor: colors.borderSecondary,
      textStyle: { color: colors.textPrimary },
    },
    legend: {
      orient: 'vertical',
      right: 8,
      top: 'middle',
      textStyle: { color: colors.textSecondary, fontSize: 12 },
    },
    series: [
      {
        type: 'pie',
        radius: ['42%', '70%'],
        center: ['38%', '50%'],
        data,
        label: { show: false },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.4)' },
        },
      },
    ],
  };
}

// ── Sub-components ────────────────────────────────────────────────────────────

interface CountDistChartProps {
  title: string;
  metricKey: string;
  groupField: string;
  experimentId: string;
  isActive: boolean;
}

function CountDistChart({
  title,
  metricKey,
  groupField,
  experimentId,
  isActive,
}: CountDistChartProps) {
  const { data: rows = [], isLoading } = useTraceQL(
    metricKey,
    experimentId,
    { omitIterationGroupBy: true },
    { enabled: isActive }
  );

  const pieData = useMemo(() => {
    const slices = rows
      .map(r => {
        const cnt = (r[groupField] as number) ?? 0;
        return {
          value: (r.count as number) ?? 0,
          name: cnt === 0 ? '0' : `${cnt}`,
          itemStyle: { color: countColor(cnt) },
          _cnt: cnt,
        };
      })
      .sort((a, b) => a._cnt - b._cnt);
    return slices as PieSlice[];
  }, [rows, groupField]);

  const placeholder = (msg: string) => (
    <ChartPanel title={title}>
      <div
        style={{
          height: 260,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: colors.textTertiary,
        }}
      >
        {msg}
      </div>
    </ChartPanel>
  );

  if (isLoading) return placeholder('Loading…');
  if (pieData.length === 0) return placeholder('No data');

  return (
    <ChartPanel title={title}>
      <ReactECharts option={makePieOption(pieData)} style={{ height: 260 }} className="w-full" />
    </ChartPanel>
  );
}

interface BinaryChartProps {
  title: string;
  hasCount: number;
  total: number;
  hasLabel: string;
  noLabel: string;
  isLoading: boolean;
}

function BinaryChart({ title, hasCount, total, hasLabel, noLabel, isLoading }: BinaryChartProps) {
  const pieData = useMemo<PieSlice[]>(
    () => [
      { value: hasCount, name: hasLabel, itemStyle: { color: COLOR_HAS_ISSUE } },
      { value: total - hasCount, name: noLabel, itemStyle: { color: COLOR_NO_ISSUE_BINARY } },
    ],
    [hasCount, total, hasLabel, noLabel]
  );

  const placeholder = (msg: string) => (
    <ChartPanel title={title}>
      <div
        style={{
          height: 260,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: colors.textTertiary,
        }}
      >
        {msg}
      </div>
    </ChartPanel>
  );

  if (isLoading) return placeholder('Loading…');
  if (total === 0) return placeholder('No data');

  return (
    <ChartPanel title={title}>
      <ReactECharts option={makePieOption(pieData)} style={{ height: 260 }} className="w-full" />
    </ChartPanel>
  );
}

// ── Main Tab ──────────────────────────────────────────────────────────────────

interface Props {
  isActive?: boolean;
}

export default function QualityAssessmentTab({ isActive = true }: Props) {
  const { id: experimentId } = useParams<{ id: string }>();

  const { data: msgRows = [], isLoading: msgLoading } = useTraceQL(
    'message_quality_binary',
    experimentId!,
    {},
    { enabled: isActive && !!experimentId }
  );

  const { total, hasLooping, hasGibberish } = useMemo(
    () => ({
      total: msgRows.reduce((s, r) => s + ((r.trajectory_count as number) ?? 0), 0),
      hasLooping: msgRows.reduce((s, r) => s + ((r.has_looping as number) ?? 0), 0),
      hasGibberish: msgRows.reduce((s, r) => s + ((r.has_gibberish as number) ?? 0), 0),
    }),
    [msgRows]
  );

  if (!experimentId) return null;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
      <CountDistChart
        title="Tool Calls Repeat"
        metricKey="tool_calls_repeat_dist"
        groupField="turn_tool_calls_repeat_cnt"
        experimentId={experimentId}
        isActive={isActive}
      />
      <CountDistChart
        title="Tool Calls Oscillate"
        metricKey="tool_calls_oscillate_dist"
        groupField="turn_tool_calls_oscillate_cnt"
        experimentId={experimentId}
        isActive={isActive}
      />
      <BinaryChart
        title="Message Looping Detection"
        hasCount={hasLooping}
        total={total}
        hasLabel="Has Looping"
        noLabel="No Looping"
        isLoading={msgLoading}
      />
      <BinaryChart
        title="Message Gibberish Detection"
        hasCount={hasGibberish}
        total={total}
        hasLabel="Has Gibberish"
        noLabel="No Gibberish"
        isLoading={msgLoading}
      />
    </div>
  );
}
