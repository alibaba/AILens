package com.alibaba.gateway.traceql;

import java.util.List;

/**
 * TraceQL Abstract Syntax Tree node definitions.
 *
 * <p>Grammar summary:
 * <pre>
 *   query        ::= multi_filter pipeline*
 *   multi_filter ::= span_filter ('&&' span_filter)*
 *   span_filter  ::= '{' conditionExpr? '}'
 *   conditionExpr::= andExpr ('or' andExpr)*
 *   andExpr      ::= atom ('and' atom)*
 *   atom         ::= '(' conditionExpr ')' | condition
 *   condition    ::= field op value
 *   pipeline     ::= '|' (select_pipe | query_by_pipe | filter_pipe)
 * </pre>
 */
public final class TraceQLAst {

    private TraceQLAst() {}

    // ── Root ──────────────────────────────────────────────────────────────────

    /**
     * Root node of a parsed TraceQL expression.
     *
     * @param spanFilters      one or more span filter blocks
     * @param spansetOperators operators between span filters (&&, ||, =>, ->); size = spanFilters.size() - 1
     * @param pipelines        zero or more pipeline stages
     */
    public record Query(
            List<SpanFilter> spanFilters,
            List<String> spansetOperators,
            List<Pipeline> pipelines
    ) {}

    /**
     * A single '{...}' block. {@code conditions} is null for an empty {@code {}}.
     */
    public record SpanFilter(ConditionExpr conditions) {}

    // ── Condition expressions ────────────────────────────────────────────────

    public sealed interface ConditionExpr
            permits AndExpr, OrExpr, Condition {}

    /** left AND right */
    public record AndExpr(ConditionExpr left, ConditionExpr right)
            implements ConditionExpr {}

    /** left OR right */
    public record OrExpr(ConditionExpr left, ConditionExpr right)
            implements ConditionExpr {}

    /**
     * A leaf condition: {@code field op value}.
     *
     * @param field dotted field name, e.g. "service_name", "attributes.http.method"
     * @param op    one of: =, !=, >, >=, <, <=
     * @param value String, Number, or null (for null literal comparisons)
     */
    public record Condition(String field, String op, Object value)
            implements ConditionExpr {}

    // ── Pipelines ─────────────────────────────────────────────────────────────

    public sealed interface Pipeline permits SelectPipeline, QueryByPipeline, FilterPipeline {}

    /**
     * {@code | select(items...) by (groupBy...)}
     *
     * @param items   columns or aggregates to project
     * @param groupBy GROUP BY columns; empty means no grouping
     */
    public record SelectPipeline(
            List<SelectItem> items,
            List<String> groupBy
    ) implements Pipeline {}

    /** {@code | query_by(field)} – join span filters by the given field */
    public record QueryByPipeline(String field) implements Pipeline {}

    /** {@code | (conditionExpr)} – filter spans by a condition after the span filter */
    public record FilterPipeline(ConditionExpr condition) implements Pipeline {}

    // ── Select items ─────────────────────────────────────────────────────────

    public sealed interface SelectItem
            permits ExprSelectItem, CountSelectItem {}

    /**
     * A general expression select item, e.g.:
     * <ul>
     *   <li>{@code trace_id}</li>
     *   <li>{@code max(duration)}</li>
     *   <li>{@code max(duration + start_time) - min(start_time) as dur}</li>
     *   <li>{@code sum(if(x = 'y', field, 0)) as total}</li>
     * </ul>
     *
     * @param expr  the expression
     * @param alias optional SQL alias (null if not specified)
     */
    public record ExprSelectItem(SelectExpr expr, String alias) implements SelectItem {}

    /** {@code count() [as alias]} */
    public record CountSelectItem(String alias) implements SelectItem {}

    // ── Select expressions ────────────────────────────────────────────────────

    /**
     * Top-level select expression. May contain aggregates.
     * Arithmetic between two aggregates is represented as {@link ArithSelectExpr}.
     */
    public sealed interface SelectExpr
            permits AggSelectExpr, ArithSelectExpr, FieldSelectExpr, ParenSelectExpr, FuncCallSelectExpr {}

    /**
     * An aggregate call: {@code aggFunc(args...)}, e.g. {@code max(duration)}, {@code quantile(duration, 0.99)}.
     *
     * @param func one of: max, min, avg, sum, p99, p95, p50, count_distinct, quantile, first, first_ai
     * @param args one or more inner expressions (e.g. quantile takes field + percentile)
     */
    public record AggSelectExpr(String func, List<InnerExpr> args) implements SelectExpr {}

    /**
     * Arithmetic between two select-level expressions,
     * e.g. {@code max(duration + start_time) - min(start_time)}.
     *
     * @param op one of: +, -
     */
    public record ArithSelectExpr(SelectExpr left, String op, SelectExpr right)
            implements SelectExpr {}

    /**
     * A non-aggregate expression used as a select item,
     * e.g. {@code trace_id} or {@code attributes.http.method}.
     */
    public record FieldSelectExpr(InnerExpr inner) implements SelectExpr {}

    /** A parenthesised select-level expression: {@code (expr)}. */
    public record ParenSelectExpr(SelectExpr inner) implements SelectExpr {}

    /**
     * A general function call wrapping select-level expressions,
     * e.g. {@code round(avg(duration))}, {@code ceil(max(reward) * 100)}.
     *
     * @param func function name (round, ceil, floor, etc.)
     * @param args select-level expression arguments
     */
    public record FuncCallSelectExpr(String func, List<SelectExpr> args) implements SelectExpr {}

    // ── Inner expressions (inside agg functions) ──────────────────────────────

    /**
     * Expression that can appear inside an aggregate function.
     * Does NOT allow nested aggregates.
     */
    public sealed interface InnerExpr
            permits FieldInnerExpr, NumberInnerExpr, StringInnerExpr, IfInnerExpr, ArithInnerExpr, ParenInnerExpr {}

    /** A field reference, e.g. {@code duration}, {@code attributes.http.method} */
    public record FieldInnerExpr(String field) implements InnerExpr {}

    /** A numeric literal, e.g. {@code 0}, {@code 3.14}, {@code -5} */
    public record NumberInnerExpr(Object value) implements InnerExpr {}

    /** A string literal, e.g. {@code 'LLM'} */
    public record StringInnerExpr(String value) implements InnerExpr {}

    /**
     * {@code if(condition, thenExpr, elseExpr)} — maps to ClickHouse {@code if()}.
     */
    public record IfInnerExpr(ConditionExpr cond, InnerExpr thenExpr, InnerExpr elseExpr)
            implements InnerExpr {}

    /**
     * Arithmetic between two inner expressions, e.g. {@code duration + start_time}.
     *
     * @param op one of: +, -, *, /
     */
    public record ArithInnerExpr(InnerExpr left, String op, InnerExpr right)
            implements InnerExpr {}

    /** A parenthesised inner expression: {@code (expr)}. */
    public record ParenInnerExpr(InnerExpr inner) implements InnerExpr {}
}
