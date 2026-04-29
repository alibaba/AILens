package com.alibaba.gateway.api;

import com.alibaba.gateway.service.TraceQueryService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(TraceQueryController.class)
class TraceQueryControllerTest {

    @Autowired MockMvc mockMvc;
    @Autowired ObjectMapper objectMapper;
    @MockBean TraceQueryService traceQueryService;

    @Test
    void trace_query_returns_200_with_data() throws Exception {
        when(traceQueryService.query(any())).thenReturn(List.of(
                Map.of("TraceId", "abc123", "ServiceName", "example-service")
        ));

        mockMvc.perform(post("/api/v1/trace/query")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "start": 1700000000,
                                  "end":   1700003600,
                                  "query": "{service_name = 'example-service'}"
                                }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.code").value(0))
                .andExpect(jsonPath("$.data[0].TraceId").value("abc123"));
    }

    @Test
    void trace_query_returns_400_when_query_missing() throws Exception {
        mockMvc.perform(post("/api/v1/trace/query")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                { "start": 1700000000 }
                                """))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.success").value(false));
    }

    @Test
    void trace_query_works_without_start_end() throws Exception {
        when(traceQueryService.query(any())).thenReturn(List.of(
                Map.of("id", "test1")
        ));
        mockMvc.perform(post("/api/v1/trace/query")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                { "query": "{service_name = 'example-service'}" }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true));
    }

    @Test
    void stat_query_returns_prometheus_format() throws Exception {
        // Mock returns Prometheus-like format: {"result": [...]}
        Map<String, Object> metric = new LinkedHashMap<>();
        metric.put("ServiceName", "example-service");
        metric.put("__name__", "my_stat");

        Map<String, Object> series = new LinkedHashMap<>();
        series.put("metric", metric);
        series.put("values", List.of(Arrays.asList(null, "42")));

        when(traceQueryService.statQuery(any())).thenReturn(
                Map.of("result", List.of(series))
        );

        mockMvc.perform(post("/api/v1/trace/stat/query")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {
                                  "querys": [
                                    {
                                      "alias": "my_stat",
                                      "query": "{service_name = 'example-service'} | select(count()) by (service_name)"
                                    }
                                  ]
                                }
                                """))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.success").value(true))
                .andExpect(jsonPath("$.data.result[0].metric.__name__").value("my_stat"));
    }
}
