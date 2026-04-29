package com.alibaba.gateway.repository;

import com.alibaba.gateway.traceql.TraceQLAst;

import java.util.List;
import java.util.Map;

/**
 * Storage-agnostic repository for querying span data.
 */
public interface SpanRepository {

    /**
     * Query spans matching the given TraceQL AST.
     *
     * @param query    parsed TraceQL AST
     * @param startSec start time (Unix seconds)
     * @param endSec   end time (Unix seconds)
     * @param limit    max rows (ignored for aggregation)
     * @param scope    data scope, e.g. "otlp", "rl", "all"
     * @return list of span rows as column→value maps
     */
    List<Map<String, Object>> query(
            TraceQLAst.Query query,
            long startSec,
            long endSec,
            int limit,
            String scope
    );
}
