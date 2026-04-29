package com.alibaba.gateway.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.HashMap;
import java.util.Map;

@Data
@ConfigurationProperties(prefix = "traceql")
public class ViewProperties {
    /**
     * Maps view name → TraceQL query string.
     * e.g. my_view → "{service_name = 'buy2'} | select(avg(duration)) by (service_name)"
     */
    private Map<String, String> views = new HashMap<>();
}
