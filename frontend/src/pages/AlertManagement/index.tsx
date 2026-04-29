import { useState, useMemo } from 'react';
import clsx from 'clsx';
import {
  Tabs,
  Table,
  Drawer,
  Button,
  Switch,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  message,
} from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import {
  useActiveAlerts,
  useAlertRules,
  useCreateAlertRule,
  type AlertItem,
  type AlertRule,
  type CreateRulePayload,
} from '../../api/alerts';
import { colors } from '../../styles/theme';
import styles from './styles.module.css';

// ── Helpers ──

function timeAgo(isoStr: string): string {
  const diff = Date.now() - new Date(isoStr).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

const SEVERITY_ORDER: Record<string, number> = { critical: 0, warning: 1, info: 2 };

function SeverityDot({ severity }: { severity: string }) {
  const key = ['critical', 'warning', 'info'].includes(severity) ? severity : 'default';
  return <span className={styles.severityDot} data-severity={key} />;
}

// ── Active Alerts tab ──

function ActiveAlertsTab() {
  const { data, isLoading } = useActiveAlerts();
  const [drawerAlert, setDrawerAlert] = useState<AlertItem | null>(null);

  const items = useMemo(() => {
    const list = data?.items ?? [];
    return [...list].sort(
      (a, b) => (SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9)
    );
  }, [data]);

  // Severity counts
  const counts = useMemo(() => {
    const c: Record<string, number> = { critical: 0, warning: 0, info: 0 };
    for (const a of items) c[a.severity] = (c[a.severity] ?? 0) + 1;
    return c;
  }, [items]);

  const columns: ColumnsType<AlertItem> = [
    {
      title: 'SEVERITY',
      dataIndex: 'severity',
      width: 100,
      render: (s: string) => (
        <span
          className={clsx(styles.severityCell, {
            'tone-error': s === 'critical',
            'tone-warning': s === 'warning',
            'tone-info': s === 'info',
            'text-tertiary': s !== 'critical' && s !== 'warning' && s !== 'info',
          })}
        >
          <SeverityDot severity={s} />
          {s}
        </span>
      ),
    },
    {
      title: 'ALERT NAME',
      dataIndex: 'rule_name',
      render: (name: string) => <span className={styles.cellName}>{name}</span>,
    },
    {
      title: 'AGENT',
      dataIndex: 'agent_name',
      width: 160,
      render: (name: string) => <span className={styles.cellAgent}>{name}</span>,
    },
    {
      title: 'FIRING SINCE',
      dataIndex: 'firing_since',
      width: 140,
      render: (ts: string) => <span className={styles.cellTime}>{timeAgo(ts)}</span>,
    },
  ];

  return (
    <>
      {/* Summary bar */}
      <div className={styles.summaryBar}>
        <span className="tone-error">🔴 {counts.critical} Critical</span>
        <span className="tone-warning">🟡 {counts.warning} Warning</span>
        <span className="tone-info">🔵 {counts.info} Info</span>
        <span className="text-tertiary">Total: {items.length}</span>
      </div>

      <Table<AlertItem>
        rowKey="id"
        columns={columns}
        dataSource={items}
        loading={isLoading}
        pagination={false}
        size="small"
        onRow={record => ({
          onClick: () => setDrawerAlert(record),
          className: styles.tableRowClick,
        })}
      />

      {/* Detail drawer */}
      <Drawer
        title={drawerAlert?.rule_name ?? 'Alert Detail'}
        open={!!drawerAlert}
        onClose={() => setDrawerAlert(null)}
        width={420}
        styles={{
          header: {
            backgroundColor: colors.panelBg,
            borderBottom: `1px solid ${colors.borderSecondary}`,
            color: colors.textPrimary,
          },
          body: { backgroundColor: colors.pageBg, padding: 24 },
        }}
      >
        {drawerAlert && (
          <div className={styles.drawerBody}>
            <div className={styles.drawerBlock}>
              <div className={styles.drawerLabel}>Alert Name</div>
              <div className={styles.drawerValueStrong}>{drawerAlert.rule_name}</div>
            </div>
            <div className={styles.drawerBlock}>
              <div className={styles.drawerLabel}>Expression</div>
              <div className={styles.drawerMonoSm}>(rule: {drawerAlert.rule_id})</div>
            </div>
            <div className={styles.drawerBlock}>
              <div className={styles.drawerLabel}>Current Value vs Threshold</div>
              <div>
                <span className={styles.drawerMetricError}>{drawerAlert.current_value}</span>
                <span className={styles.drawerSlash}>/</span>
                <span className={styles.drawerMetricMuted}>{drawerAlert.threshold}</span>
              </div>
            </div>
            <div className={styles.drawerBlock}>
              <div className={styles.drawerLabel}>Severity</div>
              <span
                className={clsx(styles.drawerSeverity, {
                  'tone-error': drawerAlert.severity === 'critical',
                  'tone-warning': drawerAlert.severity === 'warning',
                  'tone-info': drawerAlert.severity === 'info',
                  'text-tertiary':
                    drawerAlert.severity !== 'critical' &&
                    drawerAlert.severity !== 'warning' &&
                    drawerAlert.severity !== 'info',
                })}
              >
                <SeverityDot severity={drawerAlert.severity} />
                {drawerAlert.severity}
              </span>
            </div>
            <div className={styles.drawerBlockLoose}>
              <div className={styles.drawerLabel}>Firing Since</div>
              <div className={styles.drawerFiringMono}>
                {new Date(drawerAlert.firing_since).toLocaleString()} (
                {timeAgo(drawerAlert.firing_since)})
              </div>
            </div>

            {/* Silence buttons */}
            <Space>
              <Button
                onClick={() => {
                  console.log(`[Silence] Alert ${drawerAlert.id} for 1h`);
                  message.success('Silenced for 1 hour (mock)');
                }}
              >
                Silence 1h
              </Button>
              <Button
                onClick={() => {
                  console.log(`[Silence] Alert ${drawerAlert.id} for 4h`);
                  message.success('Silenced for 4 hours (mock)');
                }}
              >
                Silence 4h
              </Button>
            </Space>
          </div>
        )}
      </Drawer>
    </>
  );
}

// ── Rules tab ──

function RulesTab() {
  const { data, isLoading } = useAlertRules();
  const createMutation = useCreateAlertRule();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [form] = Form.useForm<CreateRulePayload>();

  const columns: ColumnsType<AlertRule> = [
    {
      title: 'NAME',
      dataIndex: 'name',
      render: (name: string) => <span className={styles.ruleNameCell}>{name}</span>,
    },
    {
      title: 'EXPRESSION',
      dataIndex: 'expression',
      ellipsis: true,
      render: (expr: string) => <span className={styles.ruleExprCell}>{expr}</span>,
    },
    {
      title: 'THRESHOLD',
      dataIndex: 'threshold',
      width: 100,
      render: (v: number) => <span className={styles.ruleThresholdCell}>{v}</span>,
    },
    {
      title: 'SEVERITY',
      dataIndex: 'severity',
      width: 100,
      render: (s: string) => (
        <span
          className={clsx(styles.severityCell, {
            'tone-error': s === 'critical',
            'tone-warning': s === 'warning',
            'tone-info': s === 'info',
            'text-tertiary': s !== 'critical' && s !== 'warning' && s !== 'info',
          })}
        >
          <SeverityDot severity={s} />
          {s}
        </span>
      ),
    },
    {
      title: 'ENABLED',
      dataIndex: 'enabled',
      width: 80,
      render: (enabled: boolean) => (
        <Switch
          checked={enabled}
          size="small"
          onChange={checked => console.log('Toggle rule enabled:', checked)}
        />
      ),
    },
  ];

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await createMutation.mutateAsync(values);
      message.success('Rule created');
      setDrawerOpen(false);
      form.resetFields();
    } catch {
      // validation errors are shown inline
    }
  };

  return (
    <>
      <div className={styles.rulesToolbar}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setDrawerOpen(true)}
          className={styles.primaryButton}
        >
          New Rule
        </Button>
      </div>

      <Table<AlertRule>
        rowKey="id"
        columns={columns}
        dataSource={data?.items ?? []}
        loading={isLoading}
        pagination={false}
        size="small"
      />

      {/* New rule drawer */}
      <Drawer
        title="Create Alert Rule"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={480}
        styles={{
          header: {
            backgroundColor: colors.panelBg,
            borderBottom: `1px solid ${colors.borderSecondary}`,
            color: colors.textPrimary,
          },
          body: { backgroundColor: colors.pageBg, padding: 24 },
        }}
        extra={
          <Button
            type="primary"
            loading={createMutation.isPending}
            onClick={handleCreate}
            className={styles.primaryButton}
          >
            Submit
          </Button>
        }
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            severity: 'warning',
            for_duration: '5m',
            notification_channels: ['dingtalk'],
          }}
        >
          <Form.Item
            name="name"
            label={<span className={styles.formLabel}>Rule Name</span>}
            rules={[{ required: true, message: 'Required' }]}
          >
            <Input placeholder="e.g. AgentLatencyHigh" />
          </Form.Item>

          <Form.Item
            name="expression"
            label={<span className={styles.formLabel}>Metric / Expression</span>}
            rules={[{ required: true, message: 'Required' }]}
          >
            <Select
              placeholder="Select metric"
              options={[
                { value: 'agent_request_latency_p99_ms > threshold', label: 'Agent P99 Latency' },
                { value: 'agent_error_rate > threshold', label: 'Agent Error Rate' },
                { value: 'agent_llm_tokens_per_min > threshold', label: 'Token Consumption' },
                { value: 'agent_request_rpm < threshold', label: 'RPM Drop' },
              ]}
            />
          </Form.Item>

          <Form.Item
            name="threshold"
            label={<span className={styles.formLabel}>Threshold</span>}
            rules={[{ required: true, message: 'Required' }]}
          >
            <InputNumber className="w-full max-w-full" placeholder="e.g. 30" />
          </Form.Item>

          <Form.Item
            name="for_duration"
            label={<span className={styles.formLabel}>For Duration</span>}
          >
            <Select
              options={[
                { value: '1m', label: '1 minute' },
                { value: '3m', label: '3 minutes' },
                { value: '5m', label: '5 minutes' },
                { value: '10m', label: '10 minutes' },
              ]}
            />
          </Form.Item>

          <Form.Item name="severity" label={<span className={styles.formLabel}>Severity</span>}>
            <Select
              options={[
                { value: 'critical', label: '🔴 Critical' },
                { value: 'warning', label: '🟡 Warning' },
                { value: 'info', label: '🔵 Info' },
              ]}
            />
          </Form.Item>

          <Form.Item
            name="notification_channels"
            label={<span className={styles.formLabel}>Notification Channels</span>}
          >
            <Select
              mode="multiple"
              options={[
                { value: 'dingtalk', label: 'DingTalk' },
                { value: 'email', label: 'Email' },
              ]}
            />
          </Form.Item>
        </Form>
      </Drawer>
    </>
  );
}

// ── Main Page ──

export default function AlertManagement() {
  return (
    <div className={styles.container}>
      <h1 className={styles.pageTitle}>Alert Management</h1>

      <Tabs
        defaultActiveKey="active"
        items={[
          {
            key: 'active',
            label: 'Active Alerts',
            children: <ActiveAlertsTab />,
          },
          {
            key: 'rules',
            label: 'Rules',
            children: <RulesTab />,
          },
        ]}
      />
    </div>
  );
}
