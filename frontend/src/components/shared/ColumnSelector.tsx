/* eslint-disable react-refresh/only-export-components */
import { useState, useCallback } from 'react';
import { Button, Checkbox, Popover } from 'antd';
import { SettingOutlined } from '@ant-design/icons';
import styles from './ColumnSelector.module.css';

interface ColumnGroup {
  title: string;
  columns: string[];
}

const COLUMN_GROUPS: ColumnGroup[] = [
  {
    title: 'Convergence',
    columns: [
      'pass_rate',
      'mean_reward',
      'reward_std',
      'reward_p5',
      'reward_p95',
      'pass_rate_delta',
      'reward_pass_correlation',
    ],
  },
  {
    title: 'Efficiency',
    columns: [
      'total_tokens',
      'mean_tokens_per_trajectory',
      'tokens_per_reward',
      'mean_duration_ms',
      'io_ratio',
      'mean_turns',
      'mean_llm_latency_ms',
    ],
  },
  {
    title: 'Quality',
    columns: ['zero_reward_rate', 'negative_reward_rate', 'max_turns_rate', 'mean_success_turns'],
  },
  {
    title: 'Behavior',
    columns: ['repeat_action_rate'],
  },
  {
    title: 'Metadata',
    columns: [
      'experiment_name',
      'status',
      'latest_step',
      'rollout_start_time',
      'total_data_items',
      'current_step_data_items',
      'sandbox_count',
      'total_trajectories',
      'model',
      'algorithm',
      'scaffolds',
    ],
  },
];

const STORAGE_KEY = 'ailens_column_selector';

const DEFAULT_COLUMNS = [
  'experiment_name',
  'status',
  'pass_rate',
  'mean_reward',
  'reward_std',
  'total_trajectories',
  'model',
  'algorithm',
  'latest_step',
  'mean_success_turns',
  'max_turns_rate',
];

interface ColumnSelectorProps {
  availableColumns: string[];
  selectedColumns: string[];
  onChange: (cols: string[]) => void;
}

function loadSavedColumns(): string[] | null {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return JSON.parse(saved);
  } catch {
    // Ignore localStorage errors
  }
  return null;
}

function saveColumns(cols: string[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cols));
  } catch {
    // Ignore localStorage errors
  }
}

export function useColumnSelector(availableColumns: string[]): {
  selectedColumns: string[];
  setSelectedColumns: (cols: string[]) => void;
} {
  const [selectedColumns, setSelectedColumnsState] = useState<string[]>(() => {
    const saved = loadSavedColumns();
    if (saved) return saved.filter(c => availableColumns.includes(c));
    return DEFAULT_COLUMNS.filter(c => availableColumns.includes(c));
  });

  const setSelectedColumns = useCallback((cols: string[]) => {
    setSelectedColumnsState(cols);
    saveColumns(cols);
  }, []);

  return { selectedColumns, setSelectedColumns };
}

export default function ColumnSelector({
  availableColumns,
  selectedColumns,
  onChange,
}: ColumnSelectorProps) {
  const handleToggle = (col: string, checked: boolean) => {
    if (checked) {
      onChange([...selectedColumns, col]);
    } else {
      onChange(selectedColumns.filter(c => c !== col));
    }
  };

  const handleSelectAll = () => {
    onChange([...availableColumns]);
  };

  const handleSelectNone = () => {
    onChange(['experiment_name']); // Always keep experiment name
  };

  const content = (
    <div className={styles.scrollArea}>
      <div className={styles.toolbar}>
        <Button size="small" onClick={handleSelectAll}>
          Select All
        </Button>
        <Button size="small" onClick={handleSelectNone}>
          Select None
        </Button>
      </div>
      {COLUMN_GROUPS.map(group => {
        const groupCols = group.columns.filter(c => availableColumns.includes(c));
        if (groupCols.length === 0) return null;
        return (
          <div key={group.title} className={styles.group}>
            <div className={styles.groupTitle}>{group.title}</div>
            {groupCols.map(col => (
              <div key={col} className={styles.checkboxRow}>
                <Checkbox
                  checked={selectedColumns.includes(col)}
                  onChange={e => handleToggle(col, e.target.checked)}
                >
                  <span className={styles.columnLabel}>{col.replace(/_/g, ' ')}</span>
                </Checkbox>
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );

  return (
    <Popover content={content} title="Select Columns" trigger="click" placement="bottomRight">
      <Button icon={<SettingOutlined />} size="small">
        Columns ({selectedColumns.length})
      </Button>
    </Popover>
  );
}
