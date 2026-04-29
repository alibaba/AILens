-- OTEL Logs table (source for RL trajectory data)
CREATE TABLE IF NOT EXISTS default.otel_logs
(
    `Timestamp`          DateTime64(9) CODEC(Delta(8), ZSTD(1)),
    `TimestampTime`      DateTime DEFAULT toDateTime(Timestamp),
    `TraceId`            String CODEC(ZSTD(1)),
    `SpanId`             String CODEC(ZSTD(1)),
    `TraceFlags`         UInt8,
    `SeverityText`       LowCardinality(String) CODEC(ZSTD(1)),
    `SeverityNumber`     UInt8,
    `ServiceName`        LowCardinality(String) CODEC(ZSTD(1)),
    `Body`               String CODEC(ZSTD(1)),
    `ResourceSchemaUrl`  LowCardinality(String) CODEC(ZSTD(1)),
    `ResourceAttributes` Map(LowCardinality(String), String) CODEC(ZSTD(1)),
    `ScopeSchemaUrl`     LowCardinality(String) CODEC(ZSTD(1)),
    `ScopeName`          String CODEC(ZSTD(1)),
    `ScopeVersion`       LowCardinality(String) CODEC(ZSTD(1)),
    `ScopeAttributes`    Map(LowCardinality(String), String) CODEC(ZSTD(1)),
    `LogAttributes`      Map(LowCardinality(String), String) CODEC(ZSTD(1)),
    `EventName`          String CODEC(ZSTD(1)),
    INDEX idx_trace_id TraceId TYPE bloom_filter(0.001) GRANULARITY 1,
    INDEX idx_res_attr_key mapKeys(ResourceAttributes) TYPE bloom_filter(0.01) GRANULARITY 1,
    INDEX idx_res_attr_value mapValues(ResourceAttributes) TYPE bloom_filter(0.01) GRANULARITY 1,
    INDEX idx_log_attr_key mapKeys(LogAttributes) TYPE bloom_filter(0.01) GRANULARITY 1,
    INDEX idx_log_attr_value mapValues(LogAttributes) TYPE bloom_filter(0.01) GRANULARITY 1,
    INDEX idx_body Body TYPE tokenbf_v1(32768, 3, 0) GRANULARITY 8
)
ENGINE = MergeTree
PARTITION BY toDate(TimestampTime)
PRIMARY KEY (ServiceName, TimestampTime)
ORDER BY (ServiceName, TimestampTime, Timestamp)
TTL TimestampTime + toIntervalDay(30)
SETTINGS index_granularity = 8192, ttl_only_drop_parts = 1;

-- RL Traces materialized view — extracts RL fields from otel_logs LogAttributes
-- To apply changes to an existing cluster:
--   DROP TABLE IF EXISTS default.rl_traces;
--   then re-run this CREATE.
CREATE MATERIALIZED VIEW IF NOT EXISTS default.rl_traces
ENGINE = MergeTree()
ORDER BY (experiment_id, model, iteration)
AS SELECT
    LogAttributes['id']                                              AS id,
    toInt64(toUnixTimestamp64Milli(Timestamp))                       AS start_time,
    LogAttributes['experiment_id']                                   AS experiment_id,
    toInt32OrZero(LogAttributes['iteration'])                        AS iteration,
    LogAttributes['task_id']                                         AS task_id,
    LogAttributes['dataset_name']                                    AS dataset_name,
    LogAttributes['task_language']                                   AS task_language,
    LogAttributes['tool_schema']                                     AS tool_schema,
    LogAttributes['scaffold']                                        AS scaffold,
    LogAttributes['model']                                           AS model,
    toFloat64OrZero(LogAttributes['reward'])                         AS reward,
    toInt64OrZero(LogAttributes['duration_ms'])                      AS duration_ms,
    toInt64OrZero(LogAttributes['total_tokens'])                     AS total_tokens,
    toInt64OrZero(LogAttributes['input_tokens'])                     AS input_tokens,
    toInt64OrZero(LogAttributes['output_tokens'])                    AS output_tokens,
    toInt64OrZero(LogAttributes['cache_tokens'])                     AS cache_tokens,
    LogAttributes['run_code']                                        AS run_code,
    toInt64OrZero(LogAttributes['run_duration_ms'])                  AS run_duration_ms,
    toInt64OrZero(LogAttributes['sandbox_create_duration_ms'])       AS sandbox_create_duration_ms,
    toInt32OrZero(LogAttributes['turns'])                            AS turns,
    LogAttributes['turn_format_subcategory']                         AS turn_format_subcategory,
    toInt32OrZero(LogAttributes['turn_message_gibberish_cnt'])       AS turn_message_gibberish_cnt,
    toInt32OrZero(LogAttributes['turn_message_looping_cnt'])         AS turn_message_looping_cnt,
    toInt32OrZero(LogAttributes['turn_tool_calls_oscillate_cnt'])    AS turn_tool_calls_oscillate_cnt,
    toInt32OrZero(LogAttributes['turn_tool_calls_repeat_cnt'])       AS turn_tool_calls_repeat_cnt,
    LogAttributes['verify_code']                                     AS verify_code,
    toInt64OrZero(LogAttributes['verify_duration_ms'])               AS verify_duration_ms,
    LogAttributes['tool_calls']                                      AS tool_calls,
    LogAttributes['trajectory']                                      AS trajectory
FROM otel_logs
WHERE LogAttributes['experiment_id'] != '';
