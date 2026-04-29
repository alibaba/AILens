package com.alibaba.gateway.repository.clickhouse;

import com.alibaba.gateway.core.ClickHouseQueryExecutor;
import com.alibaba.gateway.core.FieldMapper;
import com.alibaba.gateway.core.FieldMapperRegistry;
import com.alibaba.gateway.repository.SpanRepository;
import com.alibaba.gateway.traceql.ClickHouseSqlGenerator;
import com.alibaba.gateway.traceql.TraceQLAst;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Repository;

import java.util.*;

/**
 * ClickHouse-backed span repository.
 *
 * <p>When {@code scope = "all"}, queries every configured table and deduplicates
 * results by {@code (TraceId, SpanId)}.
 */
@Repository
@RequiredArgsConstructor
@Slf4j
public class ClickHouseSpanRepository implements SpanRepository {

    private final ClickHouseQueryExecutor queryExecutor;
    private final TableRouter tableRouter;
    private final ClickHouseSqlGenerator sqlGenerator;
    private final FieldMapperRegistry fieldMapperRegistry;

    @Override
    public List<Map<String, Object>> query(
            TraceQLAst.Query query,
            long startSec,
            long endSec,
            int limit,
            String scope) {

        List<String> tables = tableRouter.resolve(scope);
        FieldMapper fieldMapper = fieldMapperRegistry.get(scope);
        List<Map<String, Object>> results = new ArrayList<>();

        for (String table : tables) {
            String sql = sqlGenerator.generate(query, table, startSec, endSec, limit, fieldMapper);
            log.debug("ClickHouse query table={}: {}", table, sql);
            try {
                results.addAll(queryExecutor.execute(sql));
            } catch (Exception e) {
                log.error("ClickHouse query failed on table={}", table, e);
                throw e;
            }
        }

        return tables.size() > 1 ? deduplicate(results) : results;
    }

    /**
     * Deduplicates by (TraceId, SpanId) when querying multiple tables.
     */
    private List<Map<String, Object>> deduplicate(List<Map<String, Object>> rows) {
        Set<String> seen = new LinkedHashSet<>();
        List<Map<String, Object>> unique = new ArrayList<>();
        for (Map<String, Object> row : rows) {
            String key = row.getOrDefault("TraceId", "") + ":" + row.getOrDefault("SpanId", "");
            if (seen.add(key)) unique.add(row);
        }
        return unique;
    }
}
