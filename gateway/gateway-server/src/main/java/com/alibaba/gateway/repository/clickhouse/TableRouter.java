package com.alibaba.gateway.repository.clickhouse;

import com.alibaba.gateway.config.ClickHouseProperties;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;

/**
 * Resolves a {@code scope} parameter to one or more ClickHouse table names.
 *
 * <ul>
 *   <li>{@code "all"} → every configured table</li>
 *   <li>any other scope → the single mapped table (throws if unknown)</li>
 * </ul>
 */
@Component
@RequiredArgsConstructor
public class TableRouter {

    private final ClickHouseProperties properties;

    public List<String> resolve(String scope) {
        Map<String, String> tables = properties.getTables();
        if ("all".equalsIgnoreCase(scope)) {
            if (tables.isEmpty()) {
                throw new IllegalStateException(
                        "No ClickHouse tables configured under clickhouse.tables");
            }
            return List.copyOf(tables.values());
        }
        String table = tables.get(scope);
        if (table == null) {
            throw new IllegalArgumentException(
                    "Unknown scope '" + scope + "'. Configured: " + tables.keySet());
        }
        return List.of(table);
    }
}
