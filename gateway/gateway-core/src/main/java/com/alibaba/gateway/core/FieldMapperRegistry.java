package com.alibaba.gateway.core;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Registry that maps scope names to {@link FieldMapper} instances.
 *
 * <p>Scopes are registered at startup (e.g., "otlp" → OtlpFieldMapper,
 * "rl" → RlFieldMapper). Unknown scopes fall back to OTLP mapping.
 */
public class FieldMapperRegistry {

    private final Map<String, FieldMapper> mappers = new ConcurrentHashMap<>();
    private final FieldMapper defaultMapper;

    public FieldMapperRegistry(FieldMapper defaultMapper) {
        this.defaultMapper = defaultMapper;
    }

    public void register(String scope, FieldMapper mapper) {
        mappers.put(scope, mapper);
    }

    /**
     * Get the field mapper for the given scope.
     * Falls back to the default mapper if the scope is not registered.
     */
    public FieldMapper get(String scope) {
        return mappers.getOrDefault(scope, defaultMapper);
    }
}
