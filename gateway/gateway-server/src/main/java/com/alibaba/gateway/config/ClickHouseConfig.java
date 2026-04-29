package com.alibaba.gateway.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(ClickHouseProperties.class)
public class ClickHouseConfig {
    // DataSource is auto-configured by Spring Boot via spring.datasource.*
}
