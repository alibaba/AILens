// src/queries/task.test.ts
import { describe, it, expect } from 'vitest';
import { buildTaskSummaryQuery, buildTaskByExperimentQuery } from './task';

// ── buildTaskSummaryQuery ──

describe('buildTaskSummaryQuery', () => {
  const EXPECTED_SELECT =
    "| select(task_id, task_language, count() as trajectory_count, count_distinct(experiment_id) as experiment_count, sum(if(verify_code='success', 1, 0)) as pass_count, sum(if(verify_code='failure', 1, 0)) as fail_count, round(avg(if(verify_code='success', 1, 0)), 4) as pass_rate, max(turns) as max_turns, min(turns) as min_turns, round(avg(turns), 2) as avg_turns, max(duration_ms) as max_duration_ms, min(duration_ms) as min_duration_ms, round(avg(duration_ms), 0) as avg_duration_ms)";
  const EXPECTED_BY = '  by (task_id)';

  it('returns empty selector when no filters', () => {
    const q = buildTaskSummaryQuery({});
    expect(q).toBe(`{}\n${EXPECTED_SELECT}\n${EXPECTED_BY}`);
  });

  it('filters by language', () => {
    const q = buildTaskSummaryQuery({ language: 'python' });
    expect(q).toBe(`{task_language="python"}\n${EXPECTED_SELECT}\n${EXPECTED_BY}`);
  });

  it('filters by single outcome', () => {
    const q = buildTaskSummaryQuery({ outcome: ['success'] });
    expect(q).toBe(`{verify_code="success"}\n${EXPECTED_SELECT}\n${EXPECTED_BY}`);
  });

  it('filters by multiple outcomes with OR', () => {
    const q = buildTaskSummaryQuery({ outcome: ['success', 'failure'] });
    expect(q).toBe(
      `{(verify_code="success" or verify_code="failure")}\n${EXPECTED_SELECT}\n${EXPECTED_BY}`
    );
  });

  it('combines language and outcome filters', () => {
    const q = buildTaskSummaryQuery({ language: 'python', outcome: ['success'] });
    expect(q).toBe(
      `{task_language="python" and verify_code="success"}\n${EXPECTED_SELECT}\n${EXPECTED_BY}`
    );
  });
});

// ── buildTaskByExperimentQuery ──

describe('buildTaskByExperimentQuery', () => {
  const EXPECTED_SELECT =
    "| select(task_id, task_language, experiment_id, count() as trajectory_count, sum(if(verify_code='success', 1, 0)) as pass_count, sum(if(verify_code='failure', 1, 0)) as fail_count, round(avg(if(verify_code='success', 1, 0)), 4) as pass_rate, max(turns) as max_turns, min(turns) as min_turns, round(avg(turns), 2) as avg_turns, max(duration_ms) as max_duration_ms, min(duration_ms) as min_duration_ms, round(avg(duration_ms), 0) as avg_duration_ms)";
  const EXPECTED_BY = '  by (task_id, experiment_id)';

  it('builds query with task_id selector and correct group-by', () => {
    const q = buildTaskByExperimentQuery('task-42');
    expect(q).toBe(`{task_id="task-42"}\n${EXPECTED_SELECT}\n${EXPECTED_BY}`);
  });

  it('includes task_id value in selector', () => {
    const q = buildTaskByExperimentQuery('my-task');
    expect(q).toContain('task_id="my-task"');
  });
});
