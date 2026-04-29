package com.alibaba.gateway.traceql;

import com.alibaba.gateway.core.FieldMapper;
import com.alibaba.gateway.core.OtlpFieldMapper;
import com.alibaba.gateway.traceql.TraceQLAst.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Converts a {@link TraceQLAst.Query} into a ClickHouse SQL string.
 *
 * <p>Field mapping (TraceQL → ClickHouse column/expression):
 * <ul>
 *   <li>trace_id       → TraceId</li>
 *   <li>span_id        → SpanId</li>
 *   <li>service_name   → ServiceName</li>
 *   <li>span_name      → SpanName</li>
 *   <li>span_kind      → SpanKind</li>
 *   <li>duration       → (Duration / 1000000)  [ns → ms]</li>
 *   <li>start_time     → toUnixTimestamp64Nano(Timestamp)  [DateTime64 → ns]</li>
 *   <li>status_code    → StatusCode</li>
 *   <li>parent_span_id → ParentSpanId</li>
 *   <li>status_message → StatusMessage</li>
 *   <li>attributes.X   → SpanAttributes['X']</li>
 *   <li>resources.X    → ResourceAttributes['X']</li>
 * </ul>
 */
public class ClickHouseSqlGenerator {

    private static final FieldMapper DEFAULT_FIELD_MAPPER = new OtlpFieldMapper();

    /** Current FieldMapper — set per generate() call via ThreadLocal for nested method access. */
    private final ThreadLocal<FieldMapper> currentMapper = ThreadLocal.withInitial(() -> DEFAULT_FIELD_MAPPER);

    private static final Map<String, String> AGG_MAP = Map.of(
            "max", "max",  "min", "min",  "avg", "avg",  "sum", "sum",
            "p99", "quantile(0.99)",
            "p95", "quantile(0.95)",
            "p50", "quantile(0.50)"
    );

    /** Maps user-friendly function names to ClickHouse function names. */
    private static final Map<String, String> FUNC_ALIAS_MAP = Map.of(
            "stddev",     "stddevPop",
            "stddev_pop", "stddevPop",
            "stddev_samp","stddevSamp",
            "variance",   "varPop",
            "var_pop",    "varPop",
            "var_samp",   "varSamp",
            "median",     "median",
            "ceil",       "ceil",
            "floor",      "floor",
            "round",      "round"
    );

    public String generate(Query query, String tableName, long startSec, long endSec, int limit) {
        return generate(query, tableName, startSec, endSec, limit, DEFAULT_FIELD_MAPPER);
    }

    public String generate(Query query, String tableName, long startSec, long endSec, int limit, FieldMapper fieldMapper) {
        currentMapper.set(fieldMapper);
        String timeFilter = fieldMapper.buildTimeFilter(startSec, endSec);

        QueryByPipeline queryBy = query.pipelines().stream()
                .filter(p -> p instanceof QueryByPipeline).map(p -> (QueryByPipeline) p)
                .findFirst().orElse(null);

        // Partition pipelines (excluding query_by) into sequential stages
        List<Pipeline> pipes = query.pipelines().stream()
                .filter(p -> !(p instanceof QueryByPipeline))
                .toList();

        // Collect filter pipelines before the first select
        int firstSelectIdx = -1;
        List<FilterPipeline> preFilters = new ArrayList<>();
        for (int i = 0; i < pipes.size(); i++) {
            if (pipes.get(i) instanceof SelectPipeline) {
                firstSelectIdx = i;
                break;
            } else if (pipes.get(i) instanceof FilterPipeline fp) {
                preFilters.add(fp);
            }
        }

        boolean isTraceQuery = queryBy != null && query.spanFilters().size() > 1;

        // No select → span query or trace query
        if (firstSelectIdx == -1) {
            if (isTraceQuery) {
                return buildTraceQuerySql(query, tableName, timeFilter, preFilters, limit);
            }
            return buildSpanQuerySql(query.spanFilters().get(0), tableName, timeFilter, preFilters, limit);
        }

        SelectPipeline firstSelect = (SelectPipeline) pipes.get(firstSelectIdx);
        boolean isAggregation = !firstSelect.groupBy().isEmpty();

        // Build first-stage SQL
        String currentSql;
        if (isAggregation) {
            currentSql = buildAggSql(query, tableName, timeFilter, firstSelect, preFilters, isTraceQuery);
        } else if (isTraceQuery) {
            currentSql = buildTraceQuerySql(query, tableName, timeFilter, preFilters, limit);
        } else {
            currentSql = buildSpanQuerySql(query.spanFilters().get(0), tableName, timeFilter, preFilters, limit);
        }

        // Process remaining pipelines as nested stages
        for (int i = firstSelectIdx + 1; i < pipes.size(); i++) {
            Pipeline p = pipes.get(i);
            if (p instanceof FilterPipeline fp) {
                currentSql = wrapWithFilter(currentSql, fp);
            } else if (p instanceof SelectPipeline sel) {
                currentSql = wrapWithSelect(currentSql, sel, limit);
            }
        }

        return currentSql;
    }

    /** Wrap SQL with a filter: SELECT * FROM (innerSql) WHERE condition */
    private String wrapWithFilter(String innerSql, FilterPipeline fp) {
        return "SELECT * FROM (" + innerSql + ") WHERE " + conditionSql(fp.condition());
    }

    /** Wrap SQL with a select/group-by: SELECT ... FROM (innerSql) GROUP BY ... */
    private String wrapWithSelect(String innerSql, SelectPipeline sel, int limit) {
        List<String> groupByCols = sel.groupBy().stream().map(f -> currentMapper.get().mapField(f)).toList();
        List<String> selectItems = sel.items().stream()
                .map(this::selectItemSql)
                .collect(Collectors.toCollection(ArrayList::new));
        List<String> missing = groupByCols.stream()
                .filter(col -> selectItems.stream().noneMatch(item -> item.equals(col)))
                .toList();
        selectItems.addAll(0, missing);

        StringBuilder sql = new StringBuilder("SELECT ")
                .append(String.join(", ", selectItems))
                .append(" FROM (").append(innerSql).append(")");
        if (!groupByCols.isEmpty()) {
            sql.append(" GROUP BY ").append(String.join(", ", groupByCols));
        }
        if (sel.groupBy().isEmpty()) {
            sql.append(" LIMIT ").append(limit);
        }
        return sql.toString();
    }

    private String buildSpanQuerySql(SpanFilter filter, String table,
                                     String timeFilter, List<FilterPipeline> filterPipelines, int limit) {
        StringBuilder sql = new StringBuilder("SELECT * FROM ").append(table);
        String where = buildWhereClause(timeFilter, filter.conditions(), filterPipelines);
        if (!where.isEmpty()) sql.append(" WHERE ").append(where);
        return sql.append(" LIMIT ").append(limit).toString();
    }

    /** Build WHERE clause from optional time filter, optional span condition, and filter pipelines. */
    private String buildWhereClause(String timeFilter, ConditionExpr spanCond,
                                     List<FilterPipeline> filterPipelines) {
        List<String> parts = new ArrayList<>();
        if (timeFilter != null) parts.add(timeFilter);
        if (spanCond != null) parts.add(conditionSql(spanCond));
        for (FilterPipeline fp : filterPipelines) parts.add(conditionSql(fp.condition()));
        return String.join(" AND ", parts);
    }

    private String buildTraceQuerySql(Query query, String table,
                                      String timeFilter, List<FilterPipeline> filterPipelines, int limit) {
        StringBuilder sql = new StringBuilder("SELECT * FROM ").append(table);
        sql.append(" WHERE ").append(timeFilter != null ? timeFilter : "1=1");
        appendSpanFilterSubqueries(sql, query, table, timeFilter);
        for (FilterPipeline fp : filterPipelines) {
            sql.append(" AND ").append(conditionSql(fp.condition()));
        }
        return sql.append(" LIMIT ").append(limit).toString();
    }

    private String buildAggSql(Query query, String table, String timeFilter,
                                SelectPipeline sel, List<FilterPipeline> filterPipelines,
                                boolean isTraceQuery) {
        List<String> groupByCols = sel.groupBy().stream().map(f -> currentMapper.get().mapField(f)).toList();
        String groupByClause = String.join(", ", groupByCols);

        List<String> selectItems = sel.items().stream()
                .map(this::selectItemSql)
                .collect(Collectors.toCollection(ArrayList::new));

        List<String> missingGroupByCols = groupByCols.stream()
                .filter(col -> selectItems.stream().noneMatch(item -> item.equals(col)))
                .toList();
        selectItems.addAll(0, missingGroupByCols);

        String selectClause = String.join(", ", selectItems);

        StringBuilder sql = new StringBuilder("SELECT ").append(selectClause)
                .append(" FROM ").append(table);
        if (timeFilter != null) {
            sql.append(" WHERE ").append(timeFilter);
        } else {
            sql.append(" WHERE 1=1");
        }

        if (isTraceQuery) {
            appendSpanFilterSubqueries(sql, query, table, timeFilter);
        } else {
            SpanFilter first = query.spanFilters().get(0);
            if (first.conditions() != null) {
                sql.append(" AND ").append(conditionSql(first.conditions()));
            }
        }

        for (FilterPipeline fp : filterPipelines) {
            sql.append(" AND ").append(conditionSql(fp.condition()));
        }

        return sql.append(" GROUP BY ").append(groupByClause).toString();
    }

    /**
     * Append TraceId IN subqueries for multi-spanset queries.
     * Supports SPAN_AND (&&) and SPAN_OR (||) operators.
     * SPAN_DIRECT (=>) and SPAN_INDIRECT (->) throw UnsupportedOperationException.
     */
    private void appendSpanFilterSubqueries(StringBuilder sql, Query query,
                                             String table, String timeFilter) {
        List<SpanFilter> filters = query.spanFilters();
        List<String> operators = query.spansetOperators();

        if (filters.size() == 1) {
            SpanFilter f = filters.get(0);
            if (f.conditions() != null) {
                sql.append(" AND TraceId IN (SELECT TraceId FROM ").append(table)
                        .append(" WHERE ");
                if (timeFilter != null) sql.append(timeFilter).append(" AND ");
                sql.append(conditionSql(f.conditions())).append(")");
            }
            return;
        }

        for (int i = 0; i < filters.size(); i++) {
            String op = i > 0 ? operators.get(i - 1) : "&&";
            if ("=>".equals(op) || "->".equals(op)) {
                throw new UnsupportedOperationException(
                        "Spanset operator '" + op + "' is not yet implemented");
            }

            // For ||, use OR between subqueries; for &&, use AND
            if (i > 0) {
                sql.append("||".equals(operators.get(i - 1)) ? " OR " : " AND ");
            } else {
                sql.append(" AND (");
            }

            sql.append("TraceId IN (SELECT TraceId FROM ").append(table)
                    .append(" WHERE ");
            List<String> subParts = new ArrayList<>();
            if (timeFilter != null) subParts.add(timeFilter);
            if (filters.get(i).conditions() != null) subParts.add(conditionSql(filters.get(i).conditions()));
            sql.append(subParts.isEmpty() ? "1=1" : String.join(" AND ", subParts));
            sql.append(")");
        }
        sql.append(")");
    }

    // ── Select item SQL ───────────────────────────────────────────────────────

    private String selectItemSql(SelectItem item) {
        return switch (item) {
            case ExprSelectItem e -> {
                String exprSql = selectExprSql(e.expr());
                String resolvedAlias = e.alias() != null ? e.alias() : autoAlias(e.expr());
                yield exprSql + (resolvedAlias != null ? " AS " + resolvedAlias : "");
            }
            case CountSelectItem c -> "count()" + alias(c.alias());
        };
    }

    private String alias(String alias) {
        return alias != null ? " AS " + alias : "";
    }

    private String autoAlias(SelectExpr expr) {
        return switch (expr) {
            case AggSelectExpr a -> {
                if (a.args().isEmpty()) yield null;
                String argName = autoAliasInner(a.args().get(0));
                yield argName != null ? a.func() + "_" + argName : null;
            }
            case ArithSelectExpr ignored -> "expr";
            case FieldSelectExpr ignored -> null;
            case ParenSelectExpr ignored -> "expr";
            case FuncCallSelectExpr f -> f.func();
        };
    }

    private String autoAliasInner(InnerExpr inner) {
        return switch (inner) {
            case FieldInnerExpr f -> switch (f.field()) {
                case "duration"   -> "duration";
                case "start_time" -> "start_time";
                default -> {
                    if (f.field().startsWith("attributes."))
                        yield f.field().substring("attributes.".length()).replace(".", "_");
                    if (f.field().startsWith("resources."))
                        yield f.field().substring("resources.".length()).replace(".", "_");
                    yield null;
                }
            };
            default -> "value";
        };
    }

    // ── Select expression SQL ─────────────────────────────────────────────────

    private String selectExprSql(SelectExpr expr) {
        return switch (expr) {
            case AggSelectExpr a -> aggCallSql(a);
            case ArithSelectExpr a -> selectExprSql(a.left()) + " " + a.op() + " " + selectExprSql(a.right());
            case FieldSelectExpr f -> innerExprSql(f.inner(), false);
            case ParenSelectExpr p -> "(" + selectExprSql(p.inner()) + ")";
            case FuncCallSelectExpr f -> {
                String funcName = FUNC_ALIAS_MAP.getOrDefault(f.func(), f.func());
                String args = f.args().stream().map(this::selectExprSql).collect(Collectors.joining(", "));
                yield funcName + "(" + args + ")";
            }
        };
    }

    /**
     * Generate SQL for aggregate function calls.
     * Handles special cases: count_distinct, quantile, first, first_ai.
     */
    private String aggCallSql(AggSelectExpr a) {
        String func = a.func();
        List<InnerExpr> args = a.args();

        return switch (func) {
            case "count_distinct" -> {
                String col = innerExprSql(args.get(0), false);
                yield "count(DISTINCT " + col + ")";
            }
            case "quantile" -> {
                // quantile(field, percentile) → quantile(percentile)(field_expr)
                String fieldSql = innerExprSql(args.get(0), true);
                String percentile = args.size() > 1 ? innerExprSql(args.get(1), false) : "0.5";
                yield "quantile(" + percentile + ")(" + fieldSql + ")";
            }
            case "first" -> {
                // first(field) → argMin(column, Timestamp)
                String col = innerExprSql(args.get(0), false);
                yield "argMin(" + col + ", Timestamp)";
            }
            case "first_ai" -> {
                // first_ai(field) → argMinIf(column, Timestamp, SpanAttributes['gen_ai.span_kind_name'] != '')
                String col = innerExprSql(args.get(0), false);
                yield "argMinIf(" + col + ", Timestamp, SpanAttributes['gen_ai.span_kind_name'] != '')";
            }
            default -> {
                // Standard agg: max, min, avg, sum, p99, p95, p50
                String fn = AGG_MAP.getOrDefault(func, func);
                String argSql = innerExprSql(args.get(0), true);
                yield fn + "(" + argSql + ")";
            }
        };
    }

    // ── Inner expression SQL ──────────────────────────────────────────────────

    private String innerExprSql(InnerExpr expr, boolean numericCtx) {
        return switch (expr) {
            case FieldInnerExpr f -> currentMapper.get().mapFieldInner(f.field(), numericCtx);
            case NumberInnerExpr n -> {
                if (n.value() == null)                      yield numericCtx ? "toInt64(0)" : "0";
                if (numericCtx) yield "toInt64(" + formatNumber(n.value()) + ")";
                // Ensure whole numbers are formatted without ".0" (e.g. 4 not 4.0)
                yield formatNumber(n.value());
            }
            case StringInnerExpr s -> "'" + s.value().replace("'", "''") + "'";
            case ArithInnerExpr a ->
                    innerExprSql(a.left(), numericCtx) + " " + a.op() + " " + innerExprSql(a.right(), numericCtx);
            case ParenInnerExpr p -> "(" + innerExprSql(p.inner(), numericCtx) + ")";
            case IfInnerExpr i -> {
                String thenSql = innerExprSql(i.thenExpr(), numericCtx);
                String elseSql = innerExprSql(i.elseExpr(), numericCtx);
                if (numericCtx) {
                    thenSql = ensureInt64(thenSql);
                    elseSql = ensureInt64(elseSql);
                }
                yield "if(" + conditionSql(i.cond()) + ", " + thenSql + ", " + elseSql + ")";
            }
        };
    }

    // ── Condition SQL ─────────────────────────────────────────────────────────

    private String conditionSql(ConditionExpr expr) {
        return switch (expr) {
            case AndExpr a -> "(" + conditionSql(a.left()) + " AND " + conditionSql(a.right()) + ")";
            case OrExpr  o -> "(" + conditionSql(o.left()) + " OR "  + conditionSql(o.right()) + ")";
            case Condition c -> buildConditionSql(c);
        };
    }

    private String buildConditionSql(Condition c) {
        String col = currentMapper.get().mapField(c.field());
        if (c.value() == null) {
            boolean isMapAttr = c.field().startsWith("attributes.") || c.field().startsWith("resources.");
            return switch (c.op()) {
                case "!=" -> isMapAttr ? col + " != ''" : col + " IS NOT NULL";
                case "="  -> isMapAttr ? col + " = ''"  : col + " IS NULL";
                default -> throw new IllegalArgumentException("Unsupported op with null: " + c.op());
            };
        }
        // Wildcard matching: * in string values → LIKE
        if (c.value() instanceof String s && s.contains("*")) {
            String likePattern = "'" + s.replace("'", "''").replace("*", "%") + "'";
            return switch (c.op()) {
                case "="  -> col + " LIKE " + likePattern;
                case "!=" -> col + " NOT LIKE " + likePattern;
                default -> col + " " + c.op() + " " + formatValue(c.value());
            };
        }
        return col + " " + c.op() + " " + formatValue(c.value());
    }

    /** Delegate to the current FieldMapper for public access (e.g., from TraceQueryService). */
    public String mapField(String field) {
        return currentMapper.get().mapField(field);
    }

    private String formatValue(Object value) {
        if (value instanceof String s) return "'" + s.replace("'", "''") + "'";
        return String.valueOf(value);
    }

    /** Format a number, ensuring whole numbers have no decimal point (4.0 → "4"). */
    private String formatNumber(Object value) {
        if (value instanceof Long l) return Long.toString(l);
        if (value instanceof Double d && d == Math.floor(d) && !Double.isInfinite(d)) {
            return Long.toString(d.longValue());
        }
        return String.valueOf(value);
    }

    private String ensureInt64(String expr) {
        return expr.startsWith("toInt64") ? expr : "toInt64(" + expr + ")";
    }

    /** Get the current FieldMapper (for use by TraceQueryService). */
    public FieldMapper getCurrentFieldMapper() {
        return currentMapper.get();
    }
}
