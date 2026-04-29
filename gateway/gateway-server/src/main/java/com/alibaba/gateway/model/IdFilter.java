package com.alibaba.gateway.model;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class IdFilter {
    @NotBlank
    private String traceId;
    private String spanId; // optional, narrows to a specific span
}
