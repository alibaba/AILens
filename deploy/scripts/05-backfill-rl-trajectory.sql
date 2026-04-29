-- Backfill script: remove stale mock rows (empty trajectory) and re-insert from updated mock SQL.
-- Run this BEFORE running 04-sample-data-rl.sql again.
--
-- Step 1: Delete old mock rows from the source table.
--   ClickHouse DELETE is a mutation (async). Run the status check below after submitting.
ALTER TABLE default.otel_logs
    DELETE WHERE LogAttributes['experiment_id'] IN ('demo_qwen72b_swebench', 'demo_glm5_java');

-- Step 2: Delete stale rows from the rl_traces materialized view backing table.
--   The MV only receives NEW inserts; it does NOT auto-delete when the source is mutated.
ALTER TABLE default.rl_traces
    DELETE WHERE experiment_id IN ('demo_qwen72b_swebench', 'demo_glm5_java');

-- Step 3: Check mutations have completed (is_done = 1) before re-inserting.
--   Run this query and wait until no rows are returned with is_done = 0.
-- SELECT mutation_id, command, is_done, latest_fail_reason
-- FROM system.mutations
-- WHERE table IN ('otel_logs', 'rl_traces') AND NOT is_done
-- ORDER BY create_time DESC;

-- Step 4: After mutations finish, run 04-sample-data-rl.sql to re-insert with realistic trajectory data.
--   The MV will auto-populate rl_traces from the new inserts.
