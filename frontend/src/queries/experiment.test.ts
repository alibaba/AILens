// src/queries/experiment.test.ts
import { describe, it, expect } from 'vitest';
import { buildExperimentQuery } from './experiment';

describe('buildExperimentQuery', () => {
  it('builds reward_stats query with experiment_id only', () => {
    const result = buildExperimentQuery('reward_stats', 'exp-001');
    expect(result).toBe(
      '{experiment_id="exp-001"}\n' +
        '| select(iteration, round(avg(reward), 4) as mean_reward, stddev(reward) as reward_std, count() as trajectory_count)\n' +
        '  by (iteration)'
    );
  });

  it('appends filter values to selector', () => {
    const result = buildExperimentQuery('reward_stats', 'exp-001', {
      filters: { scaffold: 'x', task_language: 'python' },
    });
    expect(result).toContain(
      '{experiment_id="exp-001" and scaffold="x" and task_language="python"}'
    );
  });

  it('adds splitBy fields to by clause and select dimension list', () => {
    const result = buildExperimentQuery('reward_stats', 'exp-001', { splitBy: ['scaffold'] });
    expect(result).toContain('| select(iteration, scaffold,');
    expect(result).toContain('by (iteration, scaffold)');
  });

  it('supports multiple splitBy dimensions', () => {
    const result = buildExperimentQuery('reward_stats', 'exp-001', {
      splitBy: ['scaffold', 'task_language'],
    });
    expect(result).toContain('by (iteration, scaffold, task_language)');
    expect(result).toContain('| select(iteration, scaffold, task_language,');
  });

  it('appends extraFilter for success_turns_stats', () => {
    const result = buildExperimentQuery('success_turns_stats', 'exp-001');
    expect(result).toContain('verify_code="success"');
    expect(result).toContain('count() as passed_count');
  });

  it('includes turns in by for turns_distribution', () => {
    const result = buildExperimentQuery('turns_distribution', 'exp-001');
    expect(result).toContain('by (iteration, turns)');
    expect(result).toContain('count() as total_count');
    expect(result).toContain('sum_duration_ms');
  });

  it('pass_rate query produces correct select and field name', () => {
    const result = buildExperimentQuery('pass_rate', 'exp-001', { splitBy: ['scaffold'] });
    expect(result).toContain('pass_rate');
    expect(result).toContain('count() as trajectory_count');
    expect(result).toContain('by (iteration, scaffold)');
  });

  it('numeric filter values are quoted as strings', () => {
    const result = buildExperimentQuery('reward_stats', 'exp-001', {
      filters: { iteration: 3 },
    });
    expect(result).toContain('iteration="3"');
  });

  it('throws on unknown metric key', () => {
    expect(() => buildExperimentQuery('nonexistent_metric', 'exp-001')).toThrow(
      'Unknown metric key: nonexistent_metric'
    );
  });

  it('task_effectiveness groups by task_id, task_language, dataset_name, omits iteration', () => {
    const result = buildExperimentQuery('task_effectiveness', 'exp-001', {
      omitIterationGroupBy: true,
    });
    expect(result).toBe(
      '{experiment_id="exp-001"}\n' +
        "| select(task_id, task_language, dataset_name, count() as rollout_count, sum(if(verify_code='success' or verify_code='failure', 1, 0)) as valid_count, sum(if(verify_code='success', 1, 0)) as pass_count, round(avg(if(verify_code='success', 1, 0)), 4) as pass_rate, min(if(verify_code='success', iteration, 0)) as first_pass_iteration)\n" +
        '  by (task_id, task_language, dataset_name)'
    );
  });

  it('adds scaffold filter to selector when provided for task_effectiveness', () => {
    const result = buildExperimentQuery('task_effectiveness', 'exp-001', {
      filters: { scaffold: 'react' },
      omitIterationGroupBy: true,
    });
    expect(result).toContain('scaffold="react"');
    expect(result).toContain('by (task_id, task_language, dataset_name)');
  });

  it('throws when omitIterationGroupBy=true produces an empty by() clause', () => {
    // reward_stats has no extraGroupBy; omitting iteration leaves byFields=[]
    expect(() =>
      buildExperimentQuery('reward_stats', 'exp-001', { omitIterationGroupBy: true })
    ).toThrow('empty group-by');
  });

  it('does not throw when omitIterationGroupBy=true but splitBy is provided', () => {
    expect(() =>
      buildExperimentQuery('reward_stats', 'exp-001', {
        omitIterationGroupBy: true,
        splitBy: ['scaffold'],
      })
    ).not.toThrow();
  });
});
