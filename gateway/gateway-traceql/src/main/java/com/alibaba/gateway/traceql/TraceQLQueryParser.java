package com.alibaba.gateway.traceql;

import org.antlr.v4.runtime.*;

import java.util.ArrayList;
import java.util.List;

/**
 * Public entry point for parsing TraceQL strings into {@link TraceQLAst.Query}.
 *
 * <p>Named {@code TraceQLQueryParser} to avoid collision with the ANTLR-generated
 * {@code TraceQLParser} class.
 *
 * <p>This class is stateless and thread-safe. Optionally accepts a {@link ViewRegistry}
 * to expand {@code view(name)} references at parse time.
 */
public class TraceQLQueryParser {

    private volatile ViewRegistry viewRegistry;

    public TraceQLQueryParser() {}

    public TraceQLQueryParser(ViewRegistry viewRegistry) {
        this.viewRegistry = viewRegistry;
    }

    public void setViewRegistry(ViewRegistry viewRegistry) {
        this.viewRegistry = viewRegistry;
    }

    /**
     * Parse a TraceQL expression.
     *
     * <p>If the query starts with {@code view(name)}, the view is expanded using
     * the registered definition, and any extra pipelines are appended.
     *
     * @param traceQL the query string, e.g. {@code {service_name = 'buy2'}}
     * @return the parsed AST root
     * @throws TraceQLParseException on syntax errors
     */
    public TraceQLAst.Query parse(String traceQL) {
        TraceQLParser parser = buildParser(traceQL);
        TraceQLParser.QueryContext queryCtx = parser.query();

        // Check for view(name) reference
        if (queryCtx.viewRef() != null) {
            return expandView(queryCtx, traceQL);
        }

        return (TraceQLAst.Query) new TraceQLVisitorImpl().visit(queryCtx);
    }

    private TraceQLAst.Query expandView(TraceQLParser.QueryContext queryCtx, String originalQuery) {
        String viewName = queryCtx.viewRef().IDENTIFIER().getText();

        if (viewRegistry == null) {
            throw new TraceQLParseException(
                    "View '" + viewName + "' referenced but no ViewRegistry configured in: " + originalQuery);
        }

        String viewDef = viewRegistry.lookup(viewName);
        if (viewDef == null) {
            throw new TraceQLParseException(
                    "View '" + viewName + "' not found in: " + originalQuery);
        }

        // Parse the view definition (must not itself be a view reference)
        TraceQLParser viewParser = buildParser(viewDef);
        TraceQLParser.QueryContext viewQueryCtx = viewParser.query();
        if (viewQueryCtx.viewRef() != null) {
            throw new TraceQLParseException(
                    "Nested view references are not supported. View '" + viewName
                    + "' itself references view('" + viewQueryCtx.viewRef().IDENTIFIER().getText()
                    + "') in: " + originalQuery);
        }

        TraceQLAst.Query viewQuery = (TraceQLAst.Query) new TraceQLVisitorImpl().visit(viewQueryCtx);

        // Append extra pipelines from the original query after view(name)
        List<TraceQLAst.Pipeline> extraPipelines = queryCtx.pipeline().stream()
                .map(p -> (TraceQLAst.Pipeline) new TraceQLVisitorImpl().visit(p))
                .toList();

        if (extraPipelines.isEmpty()) {
            return viewQuery;
        }

        List<TraceQLAst.Pipeline> merged = new ArrayList<>(viewQuery.pipelines());
        merged.addAll(extraPipelines);
        return new TraceQLAst.Query(viewQuery.spanFilters(), viewQuery.spansetOperators(), merged);
    }

    private TraceQLParser buildParser(String traceQL) {
        CharStream input = CharStreams.fromString(traceQL);
        TraceQLLexer lexer = new TraceQLLexer(input);
        lexer.removeErrorListeners();
        lexer.addErrorListener(errorListener(traceQL));
        TraceQLParser parser = new TraceQLParser(new CommonTokenStream(lexer));
        parser.removeErrorListeners();
        parser.addErrorListener(errorListener(traceQL));
        return parser;
    }

    private ANTLRErrorListener errorListener(String input) {
        return new BaseErrorListener() {
            @Override
            public void syntaxError(Recognizer<?, ?> recognizer, Object offendingSymbol,
                                    int line, int charPositionInLine,
                                    String msg, RecognitionException e) {
                throw new TraceQLParseException(
                        msg + " at " + line + ":" + charPositionInLine + " in: " + input);
            }
        };
    }
}
