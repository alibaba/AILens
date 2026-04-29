-- Trace Gateway - ClickHouse Schema for RL (Reinforcement Learning) Traces
-- RL data is ingested via otel-collector log protocol into otel_logs table.
-- This materialized view extracts RL trajectory fields from LogAttributes.

CREATE MATERIALIZED VIEW IF NOT EXISTS default.rl_traces
ENGINE = MergeTree()
ORDER BY (experiment_id, model, iteration)
AS SELECT
    LogAttributes['id']                                          AS id,
    toInt64(toUnixTimestamp64Milli(Timestamp))                    AS start_time,
    LogAttributes['experiment_id']                               AS experiment_id,
    toInt32OrZero(LogAttributes['iteration'])                     AS iteration,
    LogAttributes['task_id']                                     AS task_id,
    LogAttributes['task_language']                               AS task_language,
    LogAttributes['tool_schema']                                 AS tool_schema,
    LogAttributes['scaffold']                                    AS scaffold,
    LogAttributes['model']                                       AS model,
    toFloat64OrZero(LogAttributes['reward'])                    AS reward,
    toInt64OrZero(LogAttributes['duration_ms'])                   AS duration_ms,
    toInt64OrZero(LogAttributes['total_tokens'])                  AS total_tokens,
    toInt64OrZero(LogAttributes['input_tokens'])                  AS input_tokens,
    toInt64OrZero(LogAttributes['output_tokens'])                 AS output_tokens,
    LogAttributes['run_code']                                    AS run_code,
    toInt64OrZero(LogAttributes['run_duration_ms'])               AS run_duration_ms,
    toInt64OrZero(LogAttributes['sandbox_create_duration_ms'])    AS sandbox_create_duration_ms,
    toInt32OrZero(LogAttributes['turns'])                         AS turns,
    LogAttributes['verify_code']                                 AS verify_code,
    toInt64OrZero(LogAttributes['verify_duration_ms'])            AS verify_duration_ms
FROM otel_logs
WHERE LogAttributes['experiment_id'] != '';
