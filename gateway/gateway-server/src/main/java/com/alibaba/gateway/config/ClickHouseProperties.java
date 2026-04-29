package com.alibaba.gateway.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.HashMap;
import java.util.Map;

@Data
@ConfigurationProperties(prefix = "clickhouse")
public class ClickHouseProperties {
    /**
     * Maps scope name → ClickHouse table name.
     * e.g. otlp → otel_traces, rl → otel_traces_rl
     */
    private Map<String, String> tables = new HashMap<>();
}
