package com.alibaba.gateway.traceql;

import com.alibaba.gateway.traceql.TraceQLAst.*;
import org.antlr.v4.runtime.tree.ParseTree;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Converts an ANTLR4 parse tree into a {@link TraceQLAst.Query}.
 * Package-private: callers should use {@link TraceQLQueryParser}.
 */
class TraceQLVisitorImpl extends TraceQLBaseVisitor<Object> {

    @Override
    public Query visitQuery(TraceQLParser.QueryContext ctx) {
        var multiFilter = ctx.multiFilter();
        List<SpanFilter> filters = multiFilter.spanFilter().stream()
                .map(sf -> (SpanFilter) visit(sf))
                .toList();
        List<String> operators = multiFilter.spansetOperator().stream()
                .map(op -> op.getText())
                .toList();
        List<Pipeline> pipelines = ctx.pipeline().stream()
                .map(p -> (Pipeline) visit(p))
                .toList();
        return new Query(filters, operators, pipelines);
    }

    // ── Span filters ──────────────────────────────────────────────────────────

    @Override
    public SpanFilter visitTempoSpanFilter(TraceQLParser.TempoSpanFilterContext ctx) {
        ConditionExpr cond = ctx.conditionExpr() != null
                ? (ConditionExpr) visit(ctx.conditionExpr())
                : null;
        return new SpanFilter(cond);
    }

    @Override
    public SpanFilter visitPromQLSpanFilter(TraceQLParser.PromQLSpanFilterContext ctx) {
        // Convert comma-separated label matchers into an AND chain
        List<TraceQLParser.LabelMatcherContext> matchers = ctx.labelMatcherList().labelMatcher();
        ConditionExpr result = buildLabelMatcher(matchers.get(0));
        for (int i = 1; i < matchers.size(); i++) {
            result = new AndExpr(result, buildLabelMatcher(matchers.get(i)));
        }
        return new SpanFilter(result);
    }

    private Condition buildLabelMatcher(TraceQLParser.LabelMatcherContext ctx) {
        String field = buildField(ctx.field());
        String op = ctx.labelMatcherOp().getText();
        Object value = parseLabelMatcherValue(ctx.labelMatcherValue());
        return new Condition(field, op, value);
    }

    private Object parseLabelMatcherValue(TraceQLParser.LabelMatcherValueContext ctx) {
        if (ctx.NULL() != null) return null;
        if (ctx.STRING_LITERAL() != null) return unquoteSingle(ctx.STRING_LITERAL().getText());
        if (ctx.DOUBLE_STRING_LITERAL() != null) return unquoteDouble(ctx.DOUBLE_STRING_LITERAL().getText());
        return parseNumber(ctx.NUMBER().getText());
    }

    // ── Condition expressions ─────────────────────────────────────────────────

    @Override
    public ConditionExpr visitConditionExpr(TraceQLParser.ConditionExprContext ctx) {
        ConditionExpr result = (ConditionExpr) visit(ctx.andExpr(0));
        for (int i = 1; i < ctx.andExpr().size(); i++) {
            result = new OrExpr(result, (ConditionExpr) visit(ctx.andExpr(i)));
        }
        return result;
    }

    @Override
    public ConditionExpr visitAndExpr(TraceQLParser.AndExprContext ctx) {
        ConditionExpr result = (ConditionExpr) visit(ctx.atom(0));
        for (int i = 1; i < ctx.atom().size(); i++) {
            result = new AndExpr(result, (ConditionExpr) visit(ctx.atom(i)));
        }
        return result;
    }

    @Override
    public Object visitParenExpr(TraceQLParser.ParenExprContext ctx) {
        return visit(ctx.conditionExpr());
    }

    @Override
    public Object visitConditionAtom(TraceQLParser.ConditionAtomContext ctx) {
        return visit(ctx.condition());
    }

    @Override
    public Condition visitCondition(TraceQLParser.ConditionContext ctx) {
        return new Condition(
                buildField(ctx.field()),
                ctx.op().getText(),
                parseValue(ctx.value())
        );
    }

    @Override
    public Pipeline visitPipeline(TraceQLParser.PipelineContext ctx) {
        return (Pipeline) visit(ctx.pipelineFunc());
    }

    // ── Pipeline functions ────────────────────────────────────────────────────

    @Override
    public SelectPipeline visitSelectFunc(TraceQLParser.SelectFuncContext ctx) {
        List<SelectItem> items = ctx.selectItem().stream()
                .map(item -> (SelectItem) visit(item))
                .toList();
        List<String> groupBy = ctx.field().stream()
                .map(this::buildField)
                .toList();
        return new SelectPipeline(items, groupBy);
    }

    @Override
    public QueryByPipeline visitQueryByFunc(TraceQLParser.QueryByFuncContext ctx) {
        return new QueryByPipeline(buildField(ctx.field()));
    }

    @Override
    public FilterPipeline visitFilterFunc(TraceQLParser.FilterFuncContext ctx) {
        return new FilterPipeline((ConditionExpr) visit(ctx.conditionExpr()));
    }

    // ── Select items ──────────────────────────────────────────────────────────

    @Override
    public ExprSelectItem visitExprItem(TraceQLParser.ExprItemContext ctx) {
        SelectExpr expr = (SelectExpr) visit(ctx.selectExpr());
        String alias = ctx.aliasName() != null ? ctx.aliasName().getText() : null;
        return new ExprSelectItem(expr, alias);
    }

    @Override
    public CountSelectItem visitCountItem(TraceQLParser.CountItemContext ctx) {
        String alias = ctx.aliasName() != null ? ctx.aliasName().getText() : null;
        return new CountSelectItem(alias);
    }

    // ── Select expressions ────────────────────────────────────────────────────

    @Override
    public ArithSelectExpr visitSelectMul(TraceQLParser.SelectMulContext ctx) {
        return new ArithSelectExpr((SelectExpr) visit(ctx.selectExpr(0)), "*", (SelectExpr) visit(ctx.selectExpr(1)));
    }

    @Override
    public ArithSelectExpr visitSelectDiv(TraceQLParser.SelectDivContext ctx) {
        return new ArithSelectExpr((SelectExpr) visit(ctx.selectExpr(0)), "/", (SelectExpr) visit(ctx.selectExpr(1)));
    }

    @Override
    public ArithSelectExpr visitSelectAdd(TraceQLParser.SelectAddContext ctx) {
        return new ArithSelectExpr((SelectExpr) visit(ctx.selectExpr(0)), "+", (SelectExpr) visit(ctx.selectExpr(1)));
    }

    @Override
    public ArithSelectExpr visitSelectSub(TraceQLParser.SelectSubContext ctx) {
        return new ArithSelectExpr((SelectExpr) visit(ctx.selectExpr(0)), "-", (SelectExpr) visit(ctx.selectExpr(1)));
    }

    @Override
    public ParenSelectExpr visitParenSelectExpr(TraceQLParser.ParenSelectExprContext ctx) {
        return new ParenSelectExpr((SelectExpr) visit(ctx.selectExpr()));
    }

    @Override
    public AggSelectExpr visitAggCallExpr(TraceQLParser.AggCallExprContext ctx) {
        String func = ctx.aggFunc().getText();
        List<InnerExpr> args = ctx.innerExpr().stream()
                .map(ie -> (InnerExpr) visit(ie))
                .toList();
        return new AggSelectExpr(func, args);
    }

    @Override
    public FuncCallSelectExpr visitFuncCallExpr(TraceQLParser.FuncCallExprContext ctx) {
        String func = ctx.IDENTIFIER().getText();
        List<SelectExpr> args = ctx.selectExpr().stream()
                .map(se -> (SelectExpr) visit(se))
                .toList();
        return new FuncCallSelectExpr(func, args);
    }

    @Override
    public FieldSelectExpr visitLeafSelectExpr(TraceQLParser.LeafSelectExprContext ctx) {
        return new FieldSelectExpr((InnerExpr) visit(ctx.innerExpr()));
    }

    // ── Inner expressions ─────────────────────────────────────────────────────

    @Override
    public ParenInnerExpr visitParenInnerExpr(TraceQLParser.ParenInnerExprContext ctx) {
        return new ParenInnerExpr((InnerExpr) visit(ctx.innerExpr()));
    }

    @Override
    public ArithInnerExpr visitInnerAdd(TraceQLParser.InnerAddContext ctx) {
        return new ArithInnerExpr((InnerExpr) visit(ctx.innerExpr(0)), "+", (InnerExpr) visit(ctx.innerExpr(1)));
    }

    @Override
    public ArithInnerExpr visitInnerSub(TraceQLParser.InnerSubContext ctx) {
        return new ArithInnerExpr((InnerExpr) visit(ctx.innerExpr(0)), "-", (InnerExpr) visit(ctx.innerExpr(1)));
    }

    @Override
    public ArithInnerExpr visitInnerMul(TraceQLParser.InnerMulContext ctx) {
        return new ArithInnerExpr((InnerExpr) visit(ctx.innerExpr(0)), "*", (InnerExpr) visit(ctx.innerExpr(1)));
    }

    @Override
    public ArithInnerExpr visitInnerDiv(TraceQLParser.InnerDivContext ctx) {
        return new ArithInnerExpr((InnerExpr) visit(ctx.innerExpr(0)), "/", (InnerExpr) visit(ctx.innerExpr(1)));
    }

    @Override
    public IfInnerExpr visitIfExpr(TraceQLParser.IfExprContext ctx) {
        return new IfInnerExpr(
                (ConditionExpr) visit(ctx.conditionExpr()),
                (InnerExpr) visit(ctx.innerExpr(0)),
                (InnerExpr) visit(ctx.innerExpr(1))
        );
    }

    @Override
    public FieldInnerExpr visitFieldInner(TraceQLParser.FieldInnerContext ctx) {
        return new FieldInnerExpr(buildField(ctx.field()));
    }

    @Override
    public NumberInnerExpr visitNumberInner(TraceQLParser.NumberInnerContext ctx) {
        return new NumberInnerExpr(parseNumber(ctx.NUMBER().getText()));
    }

    @Override
    public NumberInnerExpr visitNegNumberInner(TraceQLParser.NegNumberInnerContext ctx) {
        Object num = parseNumber(ctx.NUMBER().getText());
        if (num instanceof Long l) return new NumberInnerExpr(-l);
        return new NumberInnerExpr(-((Double) num));
    }

    @Override
    public StringInnerExpr visitStringInner(TraceQLParser.StringInnerContext ctx) {
        return new StringInnerExpr(unquoteSingle(ctx.STRING_LITERAL().getText()));
    }

    @Override
    public StringInnerExpr visitDoubleStringInner(TraceQLParser.DoubleStringInnerContext ctx) {
        return new StringInnerExpr(unquoteDouble(ctx.DOUBLE_STRING_LITERAL().getText()));
    }

    @Override
    public NumberInnerExpr visitNullInner(TraceQLParser.NullInnerContext ctx) {
        return new NumberInnerExpr(null);
    }

    // ── helpers ───────────────────────────────────────────────────────────────

    /** Joins dotted identifier segments: attributes . http . method → "attributes.http.method" */
    private String buildField(TraceQLParser.FieldContext ctx) {
        return ctx.IDENTIFIER().stream()
                .map(ParseTree::getText)
                .collect(Collectors.joining("."));
    }

    private Object parseValue(TraceQLParser.ValueContext ctx) {
        if (ctx.NULL() != null) return null;
        if (ctx.STRING_LITERAL() != null) return unquoteSingle(ctx.STRING_LITERAL().getText());
        if (ctx.DOUBLE_STRING_LITERAL() != null) return unquoteDouble(ctx.DOUBLE_STRING_LITERAL().getText());
        String num = ctx.NUMBER().getText();
        Object parsed = parseNumber(num);
        if (ctx.MINUS() != null) {
            return parsed instanceof Long l ? -l : -((Double) parsed);
        }
        return parsed;
    }

    private Object parseNumber(String text) {
        return text.contains(".") ? Double.parseDouble(text) : Long.parseLong(text);
    }

    private String unquoteSingle(String raw) {
        return raw.substring(1, raw.length() - 1).replace("\\'", "'");
    }

    private String unquoteDouble(String raw) {
        return raw.substring(1, raw.length() - 1).replace("\\\"", "\"");
    }
}
