package com.alibaba.gateway.traceql;

import com.alibaba.gateway.core.FieldMapper;
import com.alibaba.gateway.core.OtlpFieldMapper;
import com.alibaba.gateway.core.RlFieldMapper;
import org.testng.annotations.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ClickHouseSqlGeneratorTest {

    private final TraceQLQueryParser parser = new TraceQLQueryParser();
    private final ClickHouseSqlGenerator gen = new ClickHouseSqlGenerator();
    private final FieldMapper rlMapper = new RlFieldMapper();

    private static final String TABLE = "otel_traces";
    private static final long START = 1700000000L;
    private static final long END   = 1700003600L;
    private static final int  LIMIT = 100;

    private String sql(String traceQL) {
        return gen.generate(parser.parse(traceQL), TABLE, START, END, LIMIT);
    }

    // ── Backward-compatible tests ─────────────────────────────────────────────

    @Test
    void generates_simple_span_query() {
        String sql = sql("{service_name = 'buy2'}");
        assertThat(sql).containsIgnoringCase("SELECT *");
        assertThat(sql).containsIgnoringCase("FROM " + TABLE);
        assertThat(sql).containsIgnoringCase("ServiceName = 'buy2'");
        assertThat(sql).containsIgnoringCase("LIMIT " + LIMIT);
    }

    @Test
    void maps_duration_to_ms_expression() {
        assertThat(sql("{duration > 500}")).contains("(Duration / 1000000) > 500");
    }

    @Test
    void maps_attributes_to_map_access() {
        assertThat(sql("{attributes.http.method = 'GET'}")).contains("SpanAttributes['http.method'] = 'GET'");
    }

    @Test
    void generates_aggregation_with_group_by() {
        String sql = sql("{service_name = 'buy2'} | select(trace_id, max(duration), count()) by (trace_id)");
        assertThat(sql).containsIgnoringCase("GROUP BY TraceId");
        assertThat(sql).containsIgnoringCase("max(Duration / 1000000)");
        assertThat(sql).containsIgnoringCase("count()");
        assertThat(sql).doesNotContainIgnoringCase("LIMIT");
    }

    @Test
    void maps_p99_to_quantile() {
        assertThat(sql("{service_name = 's'} | select(p99(duration)) by (service_name)"))
                .containsIgnoringCase("quantile(0.99)(Duration / 1000000)");
    }

    @Test
    void generates_trace_query_with_in_subqueries() {
        String sql = sql("{service_name = 'a'} && {service_name = 'b'} | query_by(trace_id)");
        assertThat(sql.indexOf("TraceId IN")).isNotEqualTo(sql.lastIndexOf("TraceId IN"));
        assertThat(sql).contains("ServiceName = 'a'");
        assertThat(sql).contains("ServiceName = 'b'");
    }

    @Test
    void escapes_single_quotes_in_string_values() {
        assertThat(sql("{service_name = 'o\\'clock'}")).contains("ServiceName = 'o''clock'");
    }

    // ── PromQL comma style ────────────────────────────────────────────────────

    @Test
    void generates_promql_comma_style_as_and() {
        String sql = sql("{service_name = 'buy2', status_code = 'OK'}");
        assertThat(sql).contains("ServiceName = 'buy2'");
        assertThat(sql).contains("StatusCode = 'OK'");
        assertThat(sql).containsIgnoringCase("AND");
    }

    // ── Spanset operators ─────────────────────────────────────────────────────

    @Test
    void generates_span_or_as_union() {
        String sql = sql("{service_name = 'a'} || {service_name = 'b'} | query_by(trace_id)");
        assertThat(sql).contains("TraceId IN");
        assertThat(sql).containsIgnoringCase(" OR ");
        assertThat(sql).contains("ServiceName = 'a'");
        assertThat(sql).contains("ServiceName = 'b'");
    }

    @Test
    void throws_on_span_direct_operator() {
        assertThatThrownBy(() -> sql("{service_name = 'a'} => {service_name = 'b'} | query_by(trace_id)"))
                .isInstanceOf(UnsupportedOperationException.class)
                .hasMessageContaining("=>");
    }

    @Test
    void throws_on_span_indirect_operator() {
        assertThatThrownBy(() -> sql("{service_name = 'a'} -> {service_name = 'b'} | query_by(trace_id)"))
                .isInstanceOf(UnsupportedOperationException.class)
                .hasMessageContaining("->");
    }

    // ── New aggregate functions ───────────────────────────────────────────────

    @Test
    void generates_count_distinct() {
        String sql = sql("{} | select(count_distinct(trace_id)) by (service_name)");
        assertThat(sql).contains("count(DISTINCT TraceId)");
    }

    @Test
    void generates_quantile_with_percentile() {
        String sql = sql("{} | select(quantile(duration, 0.99)) by (service_name)");
        assertThat(sql).contains("quantile(0.99)(Duration / 1000000)");
    }

    @Test
    void generates_first_as_argmin() {
        String sql = sql("{} | select(first(span_name) as rootName) by (trace_id)");
        assertThat(sql).contains("argMin(SpanName, Timestamp) AS rootName");
    }

    @Test
    void generates_first_ai_as_argminif() {
        String sql = sql("{} | select(first_ai(status_code) as aiStatus) by (trace_id)");
        assertThat(sql).contains("argMinIf(StatusCode, Timestamp, SpanAttributes['gen_ai.span_kind_name'] != '')");
        assertThat(sql).contains("AS aiStatus");
    }

    // ── Wildcard matching ─────────────────────────────────────────────────────

    @Test
    void generates_wildcard_suffix_as_like() {
        assertThat(sql("{service_name = 'com.test.*'}")).contains("ServiceName LIKE 'com.test.%'");
    }

    @Test
    void generates_wildcard_prefix_as_like() {
        assertThat(sql("{service_name = '*Service'}")).contains("ServiceName LIKE '%Service'");
    }

    @Test
    void generates_wildcard_middle_as_like() {
        assertThat(sql("{service_name = '*test*'}")).contains("ServiceName LIKE '%test%'");
    }

    @Test
    void generates_wildcard_not_equal_as_not_like() {
        assertThat(sql("{service_name != 'com.test.*'}")).contains("ServiceName NOT LIKE 'com.test.%'");
    }

    // ── Complex queries (internal compatibility) ──────────────────────────────

    @Test
    void generates_null_check_for_map_attribute() {
        assertThat(sql("{attributes.gen_ai.span_kind_name != null}"))
                .contains("SpanAttributes['gen_ai.span_kind_name'] != ''");
    }

    @Test
    void generates_empty_filter_with_select() {
        String sql = sql("{} | select(count()) by (service_name)");
        assertThat(sql).containsIgnoringCase("GROUP BY ServiceName");
        assertThat(sql).doesNotContain("AND AND");
    }

    @Test
    void generates_filter_pipeline() {
        String sql = sql("{} | (service_name = 'ads-ai') | select(count()) by (service_name)");
        assertThat(sql).contains("ServiceName = 'ads-ai'");
    }

    @Test
    void generates_complex_ai_trace_query() {
        String traceQL =
                "{resources.service.name = 'aaa'} | query_by(trace_id) | select(" +
                "trace_id as traceId, " +
                "first(span_name) as rootName, " +
                "min(start_time) as startTime, " +
                "max(duration + start_time) - min(start_time) as duration, " +
                "sum(if(attributes.gen_ai.span_kind_name = 'LLM', attributes.gen_ai.usage.input_tokens, 0)) as totalInputTokens, " +
                "quantile(duration, 0.99) as durationP99, " +
                "count() as spanNum" +
                ") by (trace_id)";
        String sql = sql(traceQL);
        assertThat(sql).contains("TraceId AS traceId");
        assertThat(sql).contains("argMin(SpanName, Timestamp) AS rootName");
        assertThat(sql).contains("quantile(0.99)(Duration / 1000000) AS durationP99");
        assertThat(sql).containsIgnoringCase("GROUP BY TraceId");
    }

    // ── Multi-level nested pipeline ───────────────────────────────────────────

    @Test
    void generates_multi_level_nested_select() {
        String sql = sql("{service_name = 'x'} | select(service_name, count() as cnt) by (service_name)" +
                " | select(service_name) by (service_name)");
        // Should produce nested subquery
        assertThat(sql).contains("FROM (SELECT");
        assertThat(sql).containsIgnoringCase("GROUP BY ServiceName");
    }

    @Test
    void generates_filter_between_selects() {
        String sql = sql("{service_name = 'x'} | select(service_name, count() as cnt) by (service_name)" +
                " | (cnt > 10)" +
                " | select(service_name) by (service_name)");
        assertThat(sql).contains("FROM (SELECT * FROM (SELECT");
        assertThat(sql).contains("cnt > 10");
    }

    // ── View syntax ───────────────────────────────────────────────────────────

    @Test
    void parses_and_expands_view() {
        ViewRegistry registry = new ViewRegistry();
        registry.register("my_view", "{service_name = 'buy2'} | select(service_name, avg(duration) as avg_dur) by (service_name)");
        TraceQLQueryParser viewParser = new TraceQLQueryParser(registry);
        var q = viewParser.parse("view(my_view) | (avg_dur > 100)");
        String sql = gen.generate(q, TABLE, START, END, LIMIT);

        // View is expanded: base query + extra filter as nested stage
        assertThat(sql).contains("ServiceName = 'buy2'");
        assertThat(sql).contains("avg_dur > 100");
        assertThat(sql).containsIgnoringCase("GROUP BY ServiceName");
    }

    @Test
    void throws_on_undefined_view() {
        TraceQLQueryParser viewParser = new TraceQLQueryParser(new ViewRegistry());
        assertThatThrownBy(() -> viewParser.parse("view(nonexistent)"))
                .isInstanceOf(TraceQLParseException.class)
                .hasMessageContaining("not found");
    }

    // ── RL scope ──────────────────────────────────────────────────────────────

    @Test
    void generates_rl_query_without_time_filter() {
        String sql = gen.generate(parser.parse("{experiment_id = 'exp001'}"),
                "rl_traces", START, END, LIMIT, rlMapper);
        assertThat(sql).contains("experiment_id = 'exp001'");
        assertThat(sql).doesNotContain("toDateTime");
        assertThat(sql).contains("FROM rl_traces");
    }

    @Test
    void generates_rl_aggregation() {
        String sql = gen.generate(
                parser.parse("{} | select(model, avg(reward) as avg_reward, count() as cnt) by (model)"),
                "rl_traces", START, END, LIMIT, rlMapper);
        assertThat(sql).doesNotContain("toDateTime");
        assertThat(sql).contains("avg(reward)");
        assertThat(sql).containsIgnoringCase("GROUP BY model");
    }
}
