package com.alibaba.gateway.model;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

import java.util.List;

@Data
public class TraceStatQueryRequest {

    private Long start;  // seconds, optional — null means no lower bound

    private Long end;    // seconds, optional — null means no upper bound

    @NotEmpty
    @Valid
    private List<StatQuery> querys;

    private String scope = "otlp";

    @Data
    public static class StatQuery {
        private String alias;

        @NotBlank
        private String query; // TraceQL with aggregation pipeline
    }
}
