package com.alibaba.gateway.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.util.List;

@Data
public class TraceQueryRequest {

    private Long start;   // seconds, optional — null means no lower bound

    private Long end;     // seconds, optional — null means no upper bound

    @NotBlank
    private String query; // TraceQL statement

    @Valid
    private List<IdFilter> idFilters;

    @JsonProperty("pageSize")
    private int pageSize = 100;

    private String scope = "otlp";

    @JsonProperty("page_size")
    public void setPageSizeSnakeCase(int pageSize) {
        this.pageSize = pageSize;
    }
}
