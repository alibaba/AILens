package com.alibaba.gateway.core;

/**
 * Maps query-language field names to storage-layer column names or expressions.
 *
 * <p>Each scope (otlp, rl, etc.) has its own {@code FieldMapper} implementation.
 * The query language parser and SQL generator use this interface to remain
 * storage-agnostic.
 */
public interface FieldMapper {

    /**
     * Map a field name to a ClickHouse column name or expression
     * for use in WHERE/condition context.
     *
     * <p>Examples (OTLP): {@code "service_name" → "ServiceName"},
     * {@code "duration" → "(Duration / 1000000)"}.
     *
     * @param field the query-language field name
     * @return the ClickHouse column name or expression
     */
    String mapField(String field);

    /**
     * Map a field name for use inside aggregate functions.
     * May apply type casts (e.g. {@code toInt64OrZero()} for Map attributes).
     *
     * @param field      the query-language field name
     * @param numericCtx true if the field is used in a numeric aggregation context
     * @return the ClickHouse expression
     */
    String mapFieldInner(String field, boolean numericCtx);

    /**
     * Build a time range filter clause, or return {@code null} if this scope
     * does not use time-based filtering.
     *
     * @param startSec start time in Unix seconds (0 = no lower bound)
     * @param endSec   end time in Unix seconds (0 = no upper bound)
     * @return SQL fragment like {@code "Timestamp >= toDateTime(X) AND Timestamp <= toDateTime(Y)"},
     *         or null if no time filter should be applied
     */
    String buildTimeFilter(long startSec, long endSec);
}
