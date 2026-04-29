package com.alibaba.gateway.core;

/**
 * Field mapper for RL (Reinforcement Learning) trajectory data.
 *
 * <p>All fields map directly to ClickHouse column names — no transformations.
 * Time-based filtering is disabled since RL data is not time-partitioned
 * in the same way as OTLP traces.
 */
public class RlFieldMapper implements FieldMapper {

    @Override
    public String mapField(String field) {
        return field;
    }

    @Override
    public String mapFieldInner(String field, boolean numericCtx) {
        return field;
    }

    @Override
    public String buildTimeFilter(long startSec, long endSec) {
        return null; // RL queries do not use time-based filtering
    }
}
