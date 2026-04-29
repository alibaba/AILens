package com.alibaba.gateway.core;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Field mapper for OTLP (OpenTelemetry) trace data.
 *
 * <p>Maps TraceQL field names to ClickHouse column names/expressions
 * following the OTLP schema conventions.
 */
public class OtlpFieldMapper implements FieldMapper {

    private static final Map<String, String> FIELD_MAP = Map.of(
            "trace_id",       "TraceId",
            "span_id",        "SpanId",
            "service_name",   "ServiceName",
            "span_name",      "SpanName",
            "span_kind",      "SpanKind",
            "status_code",    "StatusCode",
            "parent_span_id", "ParentSpanId",
            "status_message", "StatusMessage"
    );

    private static final String DURATION_EXPR     = "(Duration / 1000000)";
    private static final String DURATION_EXPR_RAW = "Duration / 1000000";
    private static final String START_TIME_EXPR   = "toUnixTimestamp64Nano(Timestamp)";

    @Override
    public String mapField(String field) {
        if ("duration".equals(field)) return DURATION_EXPR;
        if ("start_time".equals(field)) return START_TIME_EXPR;
        if (field.startsWith("attributes."))
            return "SpanAttributes['" + field.substring("attributes.".length()) + "']";
        if (field.startsWith("resources."))
            return "ResourceAttributes['" + field.substring("resources.".length()) + "']";
        return FIELD_MAP.getOrDefault(field, field);
    }

    @Override
    public String mapFieldInner(String field, boolean numericCtx) {
        if ("duration".equals(field)) return DURATION_EXPR_RAW;
        if ("start_time".equals(field)) return START_TIME_EXPR;
        if (field.startsWith("attributes.")) {
            String expr = "SpanAttributes['" + field.substring("attributes.".length()) + "']";
            return numericCtx ? "toInt64OrZero(" + expr + ")" : expr;
        }
        if (field.startsWith("resources.")) {
            String expr = "ResourceAttributes['" + field.substring("resources.".length()) + "']";
            return numericCtx ? "toInt64OrZero(" + expr + ")" : expr;
        }
        return FIELD_MAP.getOrDefault(field, field);
    }

    @Override
    public String buildTimeFilter(long startSec, long endSec) {
        List<String> parts = new ArrayList<>();
        if (startSec > 0) parts.add("Timestamp >= toDateTime(" + startSec + ")");
        if (endSec > 0)   parts.add("Timestamp <= toDateTime(" + endSec + ")");
        return parts.isEmpty() ? null : String.join(" AND ", parts);
    }
}
