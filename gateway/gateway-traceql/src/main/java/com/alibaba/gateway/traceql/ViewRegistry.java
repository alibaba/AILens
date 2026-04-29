package com.alibaba.gateway.traceql;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Registry of named TraceQL view definitions.
 *
 * <p>A view maps a short name to a full TraceQL query string.
 * When {@code view(name)} appears in a query, the parser expands it
 * to the stored query and appends any extra pipelines.
 *
 * <p>View definitions are loaded from YAML configuration at startup.
 * Nested views (a view referencing another view) are not supported.
 */
public class ViewRegistry {

    private final Map<String, String> definitions = new ConcurrentHashMap<>();

    public ViewRegistry() {}

    public ViewRegistry(Map<String, String> views) {
        if (views != null) definitions.putAll(views);
    }

    /** Register or update a view definition. */
    public void register(String name, String traceQL) {
        definitions.put(name, traceQL);
    }

    /** Look up a view definition by name. Returns null if not found. */
    public String lookup(String name) {
        return definitions.get(name);
    }

    /** Check if a view with the given name exists. */
    public boolean contains(String name) {
        return definitions.containsKey(name);
    }
}
