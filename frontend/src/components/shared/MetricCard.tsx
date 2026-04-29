import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import clsx from 'clsx';
import styles from './MetricCard.module.css';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down';
}

export default function MetricCard({ title, value, subtitle, trend }: MetricCardProps) {
  return (
    <div className={styles.root}>
      <div className={styles.title}>{title}</div>

      <div className={styles.valueRow}>
        <span className={styles.value}>{value}</span>

        {trend && (
          <span
            className={clsx(styles.trend, {
              [styles.trendUp]: trend === 'up',
              [styles.trendDown]: trend === 'down',
            })}
          >
            {trend === 'up' ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
          </span>
        )}
      </div>

      {subtitle && <div className={styles.subtitle}>{subtitle}</div>}
    </div>
  );
}
