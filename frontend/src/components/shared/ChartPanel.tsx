import type { ReactNode } from 'react';
import { colors, fontSize } from '../../styles/theme';

interface ChartPanelProps {
  title: string;
  children: ReactNode;
  extra?: ReactNode;
}

export default function ChartPanel({ title, children, extra }: ChartPanelProps) {
  return (
    <div
      style={{
        backgroundColor: colors.panelBg,
        border: `1px solid ${colors.borderSecondary}`,
        borderRadius: 8,
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 16px',
          borderBottom: `1px solid ${colors.borderSecondary}`,
        }}
      >
        <span
          style={{
            fontSize: fontSize.subtitle,
            fontWeight: 600,
            color: colors.textPrimary,
          }}
        >
          {title}
        </span>
        {extra && <div>{extra}</div>}
      </div>

      {/* Body */}
      <div style={{ padding: 16 }}>{children}</div>
    </div>
  );
}
