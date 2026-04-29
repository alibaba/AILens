// src/queries/trajectory.test.ts
import { describe, it, expect } from 'vitest';
import { buildTrajectoryListQuery, buildOutcomeStatsQuery } from './trajectory';

describe('buildTrajectoryListQuery', () => {
  it('builds query with experiment_id only', () => {
    expect(buildTrajectoryListQuery('exp-001', {})).toBe('{experiment_id="exp-001"}');
  });

  it('appends single outcome as verify_code', () => {
    expect(buildTrajectoryListQuery('e', { outcome: ['success'] })).toBe(
      '{experiment_id="e" and verify_code="success"}'
    );
  });

  it('appends multiple outcomes with OR', () => {
    expect(buildTrajectoryListQuery('e', { outcome: ['success', 'failure'] })).toBe(
      '{experiment_id="e" and (verify_code="success" or verify_code="failure")}'
    );
  });

  it('appends scaffold filter', () => {
    expect(buildTrajectoryListQuery('e', { scaffold: 'my_scaffold' })).toBe(
      '{experiment_id="e" and scaffold="my_scaffold"}'
    );
  });

  it('appends reward range filters', () => {
    expect(buildTrajectoryListQuery('e', { reward_min: 0.5, reward_max: 1.0 })).toBe(
      '{experiment_id="e" and reward>=0.5 and reward<=1}'
    );
  });

  it('appends task_id filter', () => {
    expect(buildTrajectoryListQuery('e', { task_id: 'task-42' })).toBe(
      '{experiment_id="e" and task_id="task-42"}'
    );
  });

  it('combines multiple filters', () => {
    const result = buildTrajectoryListQuery('e', {
      outcome: ['success'],
      scaffold: 'basic',
      reward_min: 0.5,
    });
    expect(result).toContain('verify_code="success"');
    expect(result).toContain('scaffold="basic"');
    expect(result).toContain('reward>=0.5');
  });

  it('ignores filter fields when value is undefined', () => {
    expect(
      buildTrajectoryListQuery('e', {
        task_id: undefined,
        scaffold: undefined,
        outcome: undefined,
        reward_min: undefined,
        reward_max: undefined,
      })
    ).toBe('{experiment_id="e"}');
  });

  it('ignores undefined filters but still applies defined ones', () => {
    const q = buildTrajectoryListQuery('e', {
      task_id: undefined,
      scaffold: 's1',
      outcome: undefined,
      reward_min: 0,
      reward_max: undefined,
    });
    expect(q).toBe('{experiment_id="e" and scaffold="s1" and reward>=0}');
  });
});

describe('buildOutcomeStatsQuery', () => {
  it('builds a select query grouped by verify_code', () => {
    expect(buildOutcomeStatsQuery('exp-001')).toBe(
      '{experiment_id="exp-001"} | select(verify_code, count() as trajectory_count) by (verify_code)'
    );
  });

  it('ignores taskId when undefined', () => {
    expect(buildOutcomeStatsQuery('exp-001', undefined)).toBe(
      '{experiment_id="exp-001"} | select(verify_code, count() as trajectory_count) by (verify_code)'
    );
  });
});
