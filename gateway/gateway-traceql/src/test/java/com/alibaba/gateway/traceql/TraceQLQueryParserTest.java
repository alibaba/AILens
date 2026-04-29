package com.alibaba.gateway.traceql;

import com.alibaba.gateway.traceql.TraceQLAst.*;
import org.testng.annotations.Test;

import static org.assertj.core.api.Assertions.*;

class TraceQLQueryParserTest {

    private final TraceQLQueryParser parser = new TraceQLQueryParser();

    // ── Basic parsing (backward compatible) ───────────────────────────────────

    @Test
    void parses_simple_condition() {
        Query q = parser.parse("{service_name = 'buy2'}");
        assertThat(q.spanFilters()).hasSize(1);
        assertThat(q.spansetOperators()).isEmpty();
        Condition cond = (Condition) q.spanFilters().get(0).conditions();
        assertThat(cond.field()).isEqualTo("service_name");
        assertThat(cond.op()).isEqualTo("=");
        assertThat(cond.value()).isEqualTo("buy2");
    }

    @Test
    void parses_and_condition() {
        Query q = parser.parse("{service_name = 'buy2' and duration > 1000}");
        AndExpr and = (AndExpr) q.spanFilters().get(0).conditions();
        assertThat(((Condition) and.left()).field()).isEqualTo("service_name");
        assertThat(((Condition) and.right()).field()).isEqualTo("duration");
    }

    @Test
    void parses_nested_parens_with_or() {
        Query q = parser.parse("{a = 'x' and (b > 1 or c < 2)}");
        AndExpr and = (AndExpr) q.spanFilters().get(0).conditions();
        OrExpr or = (OrExpr) and.right();
        assertThat(((Condition) or.left()).field()).isEqualTo("b");
        assertThat(((Condition) or.right()).field()).isEqualTo("c");
    }

    @Test
    void parses_dotted_field() {
        Query q = parser.parse("{attributes.http.method = 'GET'}");
        Condition cond = (Condition) q.spanFilters().get(0).conditions();
        assertThat(cond.field()).isEqualTo("attributes.http.method");
    }

    @Test
    void parses_select_pipeline_with_group_by() {
        Query q = parser.parse(
                "{service_name = 'buy2'} | select(trace_id, max(duration), count()) by (trace_id)");
        SelectPipeline sel = (SelectPipeline) q.pipelines().get(0);
        assertThat(sel.items()).hasSize(3);
        assertThat(sel.groupBy()).containsExactly("trace_id");
    }

    @Test
    void parses_multi_filter_with_query_by() {
        Query q = parser.parse(
                "{service_name = 'buy2'} && {service_name = 'carts2'} | query_by(trace_id)");
        assertThat(q.spanFilters()).hasSize(2);
        assertThat(q.spansetOperators()).containsExactly("&&");
        assertThat(((QueryByPipeline) q.pipelines().get(0)).field()).isEqualTo("trace_id");
    }

    @Test
    void throws_on_invalid_input() {
        assertThatThrownBy(() -> parser.parse("{service_name =}"))
                .isInstanceOf(TraceQLParseException.class);
    }

    // ── PromQL comma style ────────────────────────────────────────────────────

    @Test
    void parses_promql_comma_style() {
        Query q = parser.parse("{app='metric-gateway', env='pre'}");
        assertThat(q.spanFilters()).hasSize(1);
        AndExpr and = (AndExpr) q.spanFilters().get(0).conditions();
        assertThat(((Condition) and.left()).field()).isEqualTo("app");
        assertThat(((Condition) and.left()).value()).isEqualTo("metric-gateway");
        assertThat(((Condition) and.right()).field()).isEqualTo("env");
    }

    @Test
    void parses_promql_comma_style_double_quoted() {
        Query q = parser.parse("{app=\"metric-gateway\"}");
        Condition cond = (Condition) q.spanFilters().get(0).conditions();
        assertThat(cond.value()).isEqualTo("metric-gateway");
    }

    @Test
    void parses_promql_comma_with_trailing_comma() {
        // Trailing comma is allowed (PromQL compatibility)
        Query q = parser.parse("{app='x', env='y',}");
        AndExpr and = (AndExpr) q.spanFilters().get(0).conditions();
        assertThat(((Condition) and.left()).field()).isEqualTo("app");
        assertThat(((Condition) and.right()).field()).isEqualTo("env");
    }

    // ── Spanset operators ─────────────────────────────────────────────────────

    @Test
    void parses_span_or_operator() {
        Query q = parser.parse("{service_name = 'a'} || {service_name = 'b'} | query_by(trace_id)");
        assertThat(q.spanFilters()).hasSize(2);
        assertThat(q.spansetOperators()).containsExactly("||");
    }

    @Test
    void parses_span_direct_operator() {
        Query q = parser.parse("{service_name = 'a'} => {service_name = 'b'}");
        assertThat(q.spansetOperators()).containsExactly("=>");
    }

    @Test
    void parses_span_indirect_operator() {
        Query q = parser.parse("{service_name = 'a'} -> {service_name = 'b'}");
        assertThat(q.spansetOperators()).containsExactly("->");
    }

    // ── New aggregate functions ───────────────────────────────────────────────

    @Test
    void parses_count_distinct() {
        Query q = parser.parse("{} | select(count_distinct(trace_id)) by (service_name)");
        ExprSelectItem item = (ExprSelectItem) ((SelectPipeline) q.pipelines().get(0)).items().get(0);
        AggSelectExpr agg = (AggSelectExpr) item.expr();
        assertThat(agg.func()).isEqualTo("count_distinct");
        assertThat(agg.args()).hasSize(1);
        assertThat(((FieldInnerExpr) agg.args().get(0)).field()).isEqualTo("trace_id");
    }

    @Test
    void parses_quantile_with_two_args() {
        Query q = parser.parse("{} | select(quantile(duration, 0.99)) by (service_name)");
        ExprSelectItem item = (ExprSelectItem) ((SelectPipeline) q.pipelines().get(0)).items().get(0);
        AggSelectExpr agg = (AggSelectExpr) item.expr();
        assertThat(agg.func()).isEqualTo("quantile");
        assertThat(agg.args()).hasSize(2);
        assertThat(((FieldInnerExpr) agg.args().get(0)).field()).isEqualTo("duration");
        assertThat(((NumberInnerExpr) agg.args().get(1)).value()).isEqualTo(0.99);
    }

    @Test
    void parses_first_function() {
        Query q = parser.parse("{} | select(first(name) as rootName) by (trace_id)");
        ExprSelectItem item = (ExprSelectItem) ((SelectPipeline) q.pipelines().get(0)).items().get(0);
        assertThat(item.alias()).isEqualTo("rootName");
        AggSelectExpr agg = (AggSelectExpr) item.expr();
        assertThat(agg.func()).isEqualTo("first");
    }

    @Test
    void parses_first_ai_function() {
        Query q = parser.parse("{} | select(first_ai(status_code) as aiStatus) by (trace_id)");
        ExprSelectItem item = (ExprSelectItem) ((SelectPipeline) q.pipelines().get(0)).items().get(0);
        assertThat(item.alias()).isEqualTo("aiStatus");
        AggSelectExpr agg = (AggSelectExpr) item.expr();
        assertThat(agg.func()).isEqualTo("first_ai");
    }

    // ── Null value ────────────────────────────────────────────────────────────

    @Test
    void parses_null_value_in_condition() {
        Query q = parser.parse("{a = null}");
        Condition cond = (Condition) q.spanFilters().get(0).conditions();
        assertThat(cond.value()).isNull();
    }

    @Test
    void parses_null_value_with_normal_value() {
        Query q = parser.parse("{a = null and b = '123'}");
        AndExpr and = (AndExpr) q.spanFilters().get(0).conditions();
        assertThat(((Condition) and.left()).value()).isNull();
        assertThat(((Condition) and.right()).value()).isEqualTo("123");
    }

    // ── Internal test cases compatibility ─────────────────────────────────────

    @Test
    void parses_logql_style_filter() {
        Query q = parser.parse("{} | (app = 'metric-gateway')");
        assertThat(q.spanFilters().get(0).conditions()).isNull(); // empty {}
        FilterPipeline fp = (FilterPipeline) q.pipelines().get(0);
        Condition cond = (Condition) fp.condition();
        assertThat(cond.field()).isEqualTo("app");
    }

    @Test
    void parses_logql_style_with_nested_multi_labels() {
        Query q = parser.parse("{} | ((app = 'gw' and env = 'pre') or (app = 'console' and env = 'prod'))");
        FilterPipeline fp = (FilterPipeline) q.pipelines().get(0);
        assertThat(fp.condition()).isInstanceOf(OrExpr.class);
    }

    @Test
    void parses_tempo_style_span_and_operator() {
        // LogQL style '{} | (cond) && {} | (cond)' not supported — use Tempo style instead
        Query q = parser.parse("{app = 'gw' and env = 'pre'} && {app = 'gw' and env = 'prod'}");
        assertThat(q.spanFilters()).hasSize(2);
        assertThat(q.spansetOperators()).containsExactly("&&");
    }

    @Test
    void parses_complex_ai_trace_query() {
        // This is the full AI trace query from internal test cases
        String traceQL =
                "{resources.service.name = 'aaa'} | query_by(trace_id) | select(" +
                "trace_id as traceId, " +
                "first(name) as rootName, " +
                "first_ai(status_code) as rootAiStatusCode, " +
                "min(start_time) as startTime, " +
                "max(duration + start_time) - min(start_time) as duration, " +
                "sum(if(attributes.gen_ai.span_kind_name = 'LLM', " +
                "  attributes.gen_ai.usage.input_tokens + attributes.gen_ai.usage.output_tokens, 0)) as totalTokens, " +
                "avg(duration) as avgDuration, " +
                "quantile(duration, 0.99) as durationP99, " +
                "count() as spanNum" +
                ") by (trace_id)";
        Query q = parser.parse(traceQL);
        SelectPipeline sel = (SelectPipeline) q.pipelines().get(1); // [0] = query_by, [1] = select
        assertThat(sel.items()).hasSize(9);
        assertThat(sel.groupBy()).containsExactly("trace_id");
    }
}
