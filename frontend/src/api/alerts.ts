import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from './client';

// ── Types ──

export interface AlertItem {
  id: string;
  rule_id: string;
  rule_name: string;
  severity: 'critical' | 'warning' | 'info';
  agent_name: string;
  current_value: number;
  threshold: number;
  firing_since: string;
  status: string;
  labels: Record<string, string>;
}

export interface ActiveAlertsResponse {
  total: number;
  items: AlertItem[];
}

export interface AlertRule {
  id: string;
  name: string;
  expression: string;
  threshold: number;
  severity: 'critical' | 'warning' | 'info';
  for_duration: string;
  enabled: boolean;
  notification_channels: string[];
  created_at: string;
  updated_at: string;
}

export interface AlertRulesResponse {
  items: AlertRule[];
}

export interface CreateRulePayload {
  name: string;
  expression: string;
  threshold: number;
  severity: 'critical' | 'warning' | 'info';
  for_duration: string;
  notification_channels: string[];
}

// ── Hooks ──

export function useActiveAlerts() {
  return useQuery<ActiveAlertsResponse>({
    queryKey: ['alerts-active'],
    queryFn: () => apiClient.get('/alerts/active').then(r => r.data),
    staleTime: 15_000,
    refetchInterval: 30_000,
  });
}

export function useAlertRules() {
  return useQuery<AlertRulesResponse>({
    queryKey: ['alert-rules'],
    queryFn: () => apiClient.get('/alerts/rules').then(r => r.data),
    staleTime: 60_000,
  });
}

export function useCreateAlertRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateRulePayload) =>
      apiClient.post('/alerts/rules', payload).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alert-rules'] });
    },
  });
}
