import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import type { OutcomeType } from '../../types';
import { colors, fontSize } from '../../styles/theme';

interface OutcomeBadgeProps {
  outcome: OutcomeType;
}

const outcomeConfig: Record<
  OutcomeType,
  { color: string; bgColor: string; icon: React.ReactNode; label: string }
> = {
  success: {
    color: colors.success,
    bgColor: 'rgba(34, 197, 94, 0.12)',
    icon: <CheckCircleOutlined />,
    label: 'Success',
  },
  failure: {
    color: colors.error,
    bgColor: 'rgba(239, 68, 68, 0.12)',
    icon: <CloseCircleOutlined />,
    label: 'Failure',
  },
  timeout: {
    color: colors.timeout,
    bgColor: 'rgba(168, 85, 247, 0.12)',
    icon: <ClockCircleOutlined />,
    label: 'Timeout',
  },
  error: {
    color: colors.warning,
    bgColor: 'rgba(245, 158, 11, 0.12)',
    icon: <ExclamationCircleOutlined />,
    label: 'Error',
  },
  running: {
    color: colors.info,
    bgColor: 'rgba(59, 130, 246, 0.12)',
    icon: <LoadingOutlined />,
    label: 'Running',
  },
};

export default function OutcomeBadge({ outcome }: OutcomeBadgeProps) {
  const config = outcomeConfig[outcome];

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '3px 10px',
        borderRadius: 999,
        fontSize: fontSize.sm,
        fontWeight: 500,
        color: config.color,
        backgroundColor: config.bgColor,
        lineHeight: '16px',
        whiteSpace: 'nowrap',
      }}
    >
      {config.icon}
      {config.label}
    </span>
  );
}
