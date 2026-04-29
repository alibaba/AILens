// Experiment Header Component - Filter controls only
// Experiment name/status/scaffolds/model are displayed in the TopBar

import { useNavigate, useParams } from 'react-router-dom';
import type { FormInstance } from 'antd/es/form';
import { Button, Form, Select } from 'antd';
import { type ExperimentFilterFormValues } from './experimentFilterForm';
import styles from './ExperimentHeader.module.css';

interface ExperimentHeaderProps {
  scaffolds: string[];
  languages: string[];
  toolSchemas: string[];
  form: FormInstance<ExperimentFilterFormValues>;
  showIterationFilter?: boolean;
  iterationFilter?: string;
  iterationOptions?: { label: string; value: string }[];
  onIterationChange?: (v: string) => void;
}

export default function ExperimentHeader({
  scaffolds,
  languages,
  toolSchemas,
  form,
  showIterationFilter,
  iterationFilter,
  iterationOptions,
  onIterationChange,
}: ExperimentHeaderProps) {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  return (
    <Form
      form={form}
      initialValues={{
        splitBy: 'none',
      }}
      component={false}
    >
      <div className={styles.root}>
        <div className={styles.toolbar}>
          <div className={styles.filtersLeft}>
            <div className={styles.filterRow}>
              <span>Scaffold:</span>
              <Form.Item name="scaffoldFilter" noStyle>
                <Select
                  size="small"
                  placeholder="All"
                  style={{ width: 150 }}
                  options={[
                    { value: 'all', label: 'All' },
                    ...scaffolds.map(s => ({ value: s, label: s })),
                  ]}
                />
              </Form.Item>
            </div>
            <div className={styles.filterRow}>
              <span>Language:</span>
              <Form.Item name="languageFilter" noStyle>
                <Select
                  size="small"
                  placeholder="All"
                  style={{ width: 130 }}
                  options={[
                    { value: 'all', label: 'All' },
                    ...languages.map(s => ({ value: s, label: s })),
                  ]}
                />
              </Form.Item>
            </div>
            <div className={styles.filterRow}>
              <span>Tool Schema:</span>
              <Form.Item name="toolSchemaFilter" noStyle>
                <Select
                  size="small"
                  placeholder="All"
                  style={{ width: 130 }}
                  options={[
                    { value: 'all', label: 'All' },
                    ...toolSchemas.map(s => ({ value: s, label: s })),
                  ]}
                />
              </Form.Item>
            </div>
            <div className={styles.filterRow}>
              <span>Split By:</span>
              <Form.Item name="splitBy" noStyle>
                <Select
                  size="small"
                  style={{ width: 160 }}
                  options={[
                    { value: 'none', label: 'None' },
                    { value: 'scaffold', label: 'Scaffold' },
                    { value: 'tool_schema', label: 'Tool Schema' },
                  ]}
                />
              </Form.Item>
            </div>
            {showIterationFilter && (
              <div className={styles.filterRow}>
                <span>Iteration:</span>
                <Select
                  value={iterationFilter}
                  onChange={onIterationChange}
                  options={iterationOptions}
                  size="small"
                  style={{ width: 120 }}
                />
              </div>
            )}
          </div>
          <Button
            type="primary"
            ghost
            size="small"
            onClick={() => navigate(`/experiments/${id}/trajectories`)}
          >
            Open Trajectory Explorer →
          </Button>
        </div>
      </div>
    </Form>
  );
}
