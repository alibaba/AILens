package com.alibaba.gateway.config;

import com.alibaba.gateway.core.FieldMapperRegistry;
import com.alibaba.gateway.core.OtlpFieldMapper;
import com.alibaba.gateway.core.RlFieldMapper;
import com.alibaba.gateway.traceql.ClickHouseSqlGenerator;
import com.alibaba.gateway.traceql.TraceQLQueryParser;
import com.alibaba.gateway.traceql.ViewRegistry;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(ViewProperties.class)
public class AppConfig {

    @Bean
    public FieldMapperRegistry fieldMapperRegistry() {
        OtlpFieldMapper otlpMapper = new OtlpFieldMapper();
        RlFieldMapper rlMapper = new RlFieldMapper();

        FieldMapperRegistry registry = new FieldMapperRegistry(otlpMapper);
        registry.register("otlp", otlpMapper);
        registry.register("rl", rlMapper);
        return registry;
    }

    @Bean
    public ViewRegistry viewRegistry(ViewProperties viewProperties) {
        return new ViewRegistry(viewProperties.getViews());
    }

    @Bean
    public TraceQLQueryParser traceQLQueryParser(ViewRegistry viewRegistry) {
        return new TraceQLQueryParser(viewRegistry);
    }

    @Bean
    public ClickHouseSqlGenerator clickHouseSqlGenerator() {
        return new ClickHouseSqlGenerator();
    }
}
