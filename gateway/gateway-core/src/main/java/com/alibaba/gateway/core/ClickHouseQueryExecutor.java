package com.alibaba.gateway.core;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;

/**
 * Generic ClickHouse SQL executor.
 *
 * <p>Decoupled from any specific query language (TraceQL, PromQL, etc.).
 * Handles SQL execution and logging.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class ClickHouseQueryExecutor {

    private final JdbcTemplate jdbcTemplate;

    /**
     * Execute a SQL query and return the results as a list of column→value maps.
     *
     * @param sql the ClickHouse SQL string
     * @return query results
     */
    public List<Map<String, Object>> execute(String sql) {
        log.debug("ClickHouse query: {}", sql);
        return jdbcTemplate.queryForList(sql);
    }
}
