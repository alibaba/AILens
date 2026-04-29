package com.alibaba.gateway.service;

import com.alibaba.gateway.model.IdFilter;
import com.alibaba.gateway.model.TraceQueryRequest;
import com.alibaba.gateway.model.TraceStatQueryRequest;
import com.alibaba.gateway.core.FieldMapperRegistry;
import com.alibaba.gateway.repository.SpanRepository;
import com.alibaba.gateway.traceql.TraceQLAst.*;
import com.alibaba.gateway.traceql.TraceQLQueryParser;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.util.CollectionUtils;

import java.util.*;

/**
 * Orchestrates TraceQL parsing, idFilter injection, and repository dispatch.
 */
@Service
@RequiredArgsConstructor
public class TraceQueryService {

    private final TraceQLQueryParser traceQLQueryParser;
    private final SpanRepository spanRepository;
    private final FieldMapperRegistry fieldMapperRegistry;

    public List<Map<String, Object>> query(TraceQueryRequest request) {
        Query query = traceQLQueryParser.parse(request.getQuery());

        if (!CollectionUtils.isEmpty(request.getIdFilters())) {
            query = injectIdFilters(query, request.getIdFilters());
        }

        return spanRepository.query(
                query,
                request.getStart() != null ? request.getStart() : 0L,
                request.getEnd() != null ? request.getEnd() : 0L,
                request.getPageSize(),
                request.getScope()
        );
    }

    /**
     * Execute multiple stat queries and return a single Prometheus-like result.
     *
     * <p>All queries' results are merged into one flat {@code result} array.
     * The {@code alias} of each sub-query sets the {@code __name__} label for
     * that query's series. When no alias is given, {@code __name__} defaults to
     * the first GROUP BY TraceQL field name.
     *
     * <pre>
     * {
     *   "result": [
     *     {"metric": {"dim": "value", "__name__": "alias_or_field"}, "values": [[null, "123"]]}
     *   ]
     * }
     * </pre>
     */
    public Map<String, Object> statQuery(TraceStatQueryRequest request) {
        List<Map<String, Object>> allSeries = new ArrayList<>();

        for (TraceStatQueryRequest.StatQuery sq : request.getQuerys()) {
            Query query = traceQLQueryParser.parse(sq.getQuery());
            List<Map<String, Object>> rows = spanRepository.query(
                    query,
                    request.getStart() != null ? request.getStart() : 0L,
                    request.getEnd() != null ? request.getEnd() : 0L,
                    Integer.MAX_VALUE,
                    request.getScope()
            );

            List<String> groupByFields = query.pipelines().stream()
                    .filter(p -> p instanceof SelectPipeline)
                    .map(p -> (SelectPipeline) p)
                    .findFirst()
                    .map(SelectPipeline::groupBy)
                    .orElse(List.of());

            allSeries.addAll(toPrometheusSeries(rows, groupByFields, sq.getAlias(), request.getScope()));
        }

        return Map.of("result", allSeries);
    }

    /**
     * Transform raw ClickHouse rows into Prometheus-like series entries.
     *
     * <p>One series per row. GROUP BY columns become metric dimension labels.
     * {@code __name__} = alias if provided, else the first GROUP BY TraceQL field name.
     * All aggregate values for the row are collected into the {@code values} list
     * as {@code [null, "stringValue"]} pairs (null = no timestamp in non-timeseries mode).
     */
    private List<Map<String, Object>> toPrometheusSeries(List<Map<String, Object>> rows,
                                                          List<String> groupByFields,
                                                          String alias,
                                                          String scope) {
        Set<String> dimCols = new LinkedHashSet<>();
        for (String field : groupByFields) {
            dimCols.add(fieldMapperRegistry.get(scope).mapField(field));
        }

        String metricName = alias != null
                ? alias
                : (groupByFields.isEmpty() ? "result" : groupByFields.get(0));

        List<Map<String, Object>> series = new ArrayList<>();
        for (Map<String, Object> row : rows) {
            Map<String, Object> metric = new LinkedHashMap<>();
            for (String col : dimCols) {
                Object val = row.get(col);
                if (val != null) metric.put(col, String.valueOf(val));
            }
            metric.put("__name__", metricName);

            List<List<Object>> values = new ArrayList<>();
            for (Map.Entry<String, Object> entry : row.entrySet()) {
                if (!dimCols.contains(entry.getKey())) {
                    values.add(Arrays.asList(null, String.valueOf(entry.getValue())));
                }
            }

            Map<String, Object> s = new LinkedHashMap<>();
            s.put("metric", metric);
            s.put("values", values);
            series.add(s);
        }
        return series;
    }

    /**
     * Prepend idFilter conditions (OR-combined) to the first span filter as AND.
     */
    private Query injectIdFilters(Query query, List<IdFilter> idFilters) {
        if (query.spanFilters().isEmpty()) {
            return query;
        }
        ConditionExpr idExpr = buildIdFilterExpr(idFilters);
        SpanFilter first = query.spanFilters().get(0);
        SpanFilter updated = new SpanFilter(
                first.conditions() != null
                        ? new AndExpr(idExpr, first.conditions())
                        : idExpr
        );

        List<SpanFilter> newFilters = new ArrayList<>();
        newFilters.add(updated);
        newFilters.addAll(query.spanFilters().subList(1, query.spanFilters().size()));
        return new Query(newFilters, query.spansetOperators(), query.pipelines());
    }

    private ConditionExpr buildIdFilterExpr(List<IdFilter> idFilters) {
        List<ConditionExpr> exprs = idFilters.stream().map(this::filterToExpr).toList();
        ConditionExpr result = exprs.get(0);
        for (int i = 1; i < exprs.size(); i++) {
            result = new OrExpr(result, exprs.get(i));
        }
        return result;
    }

    private ConditionExpr filterToExpr(IdFilter f) {
        Condition traceExpr = new Condition("trace_id", "=", f.getTraceId());
        if (f.getSpanId() == null || f.getSpanId().isBlank()) return traceExpr;
        return new AndExpr(traceExpr, new Condition("span_id", "=", f.getSpanId()));
    }
}
