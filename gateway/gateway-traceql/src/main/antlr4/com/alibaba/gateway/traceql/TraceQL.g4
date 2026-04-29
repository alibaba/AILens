grammar TraceQL;

// ── Parser rules ─────────────────────────────────────────────────────────────

query
    : (viewRef | multiFilter) pipeline* EOF
    ;

viewRef
    : VIEW LPAREN IDENTIFIER RPAREN
    ;

multiFilter
    : spanFilter (spansetOperator spanFilter)*
    ;

spansetOperator
    : SPAN_AND | SPAN_OR | SPAN_DIRECT | SPAN_INDIRECT
    ;

spanFilter
    : LBRACE labelMatcherList RBRACE    # promQLSpanFilter
    | LBRACE conditionExpr? RBRACE      # tempoSpanFilter
    ;

// PromQL-style comma-separated label matchers: {a='x', b='y'}
labelMatcherList
    : labelMatcher (COMMA labelMatcher)* COMMA?
    ;

labelMatcher
    : field labelMatcherOp labelMatcherValue
    ;

labelMatcherOp
    : EQ | NEQ
    ;

labelMatcherValue
    : STRING_LITERAL
    | DOUBLE_STRING_LITERAL
    | NUMBER
    | NULL
    ;

conditionExpr
    : andExpr (OR andExpr)*
    ;

andExpr
    : atom (AND atom)*
    ;

atom
    : LPAREN conditionExpr RPAREN   # parenExpr
    | condition                     # conditionAtom
    ;

condition
    : field op value
    ;

field
    : IDENTIFIER (DOT IDENTIFIER)*
    ;

op
    : EQ | NEQ | GT | GTE | LT | LTE
    ;

value
    : STRING_LITERAL
    | DOUBLE_STRING_LITERAL
    | NUMBER
    | MINUS NUMBER
    | NULL
    ;

pipeline
    : PIPE pipelineFunc
    ;

pipelineFunc
    : SELECT LPAREN selectItem (COMMA selectItem)* RPAREN
      (BY LPAREN field (COMMA field)* RPAREN)?   # selectFunc
    | QUERY_BY LPAREN field RPAREN               # queryByFunc
    | LPAREN conditionExpr RPAREN                # filterFunc
    ;

selectItem
    : selectExpr (AS aliasName)?   # exprItem
    | COUNT LPAREN RPAREN (AS aliasName)?  # countItem
    ;

// Allow keywords as alias names
aliasName
    : IDENTIFIER | COUNT | MAX | MIN | AVG | SUM | IF | AS | BY | AND | OR
    | SELECT | QUERY_BY | NULL | VIEW | P99 | P95 | P50
    | COUNT_DISTINCT | QUANTILE | FIRST | FIRST_AI
    ;

// Select-level expression: may combine aggregates with arithmetic
// Higher alternatives = higher precedence (ANTLR4 left-recursion rule)
selectExpr
    : selectExpr STAR  selectExpr   # selectMul
    | selectExpr SLASH selectExpr   # selectDiv
    | selectExpr PLUS  selectExpr   # selectAdd
    | selectExpr MINUS selectExpr   # selectSub
    | LPAREN selectExpr RPAREN      # parenSelectExpr
    | aggFunc LPAREN innerExpr (COMMA innerExpr)* RPAREN  # aggCallExpr
    | IDENTIFIER LPAREN (selectExpr (COMMA selectExpr)*)? RPAREN  # funcCallExpr
    | innerExpr                     # leafSelectExpr
    ;

// Inner expression: inside agg functions — no nested aggregates
innerExpr
    : LPAREN innerExpr RPAREN       # parenInnerExpr
    | innerExpr STAR  innerExpr     # innerMul
    | innerExpr SLASH innerExpr     # innerDiv
    | innerExpr PLUS  innerExpr     # innerAdd
    | innerExpr MINUS innerExpr     # innerSub
    | IF LPAREN conditionExpr COMMA innerExpr COMMA innerExpr RPAREN  # ifExpr
    | field                         # fieldInner
    | NUMBER                        # numberInner
    | MINUS NUMBER                  # negNumberInner
    | STRING_LITERAL                # stringInner
    | DOUBLE_STRING_LITERAL         # doubleStringInner
    | NULL                          # nullInner
    ;

aggFunc
    : MAX | MIN | AVG | SUM | P99 | P95 | P50
    | COUNT_DISTINCT | QUANTILE | FIRST | FIRST_AI
    ;

// ── Lexer rules ───────────────────────────────────────────────────────────────
// Keywords must appear before IDENTIFIER (ANTLR: first match wins on equal length)

AND      : 'and' ;
OR       : 'or' ;
BY       : 'by' ;
SELECT   : 'select' ;
QUERY_BY : 'query_by' ;
COUNT    : 'count' ;
AS       : 'as' ;
IF       : 'if' ;
NULL     : 'null' ;
MAX      : 'max' ;
MIN      : 'min' ;
AVG      : 'avg' ;
SUM      : 'sum' ;
P99      : 'p99' ;
P95      : 'p95' ;
P50      : 'p50' ;
VIEW           : 'view' ;
COUNT_DISTINCT : 'count_distinct' ;
QUANTILE       : 'quantile' ;
FIRST          : 'first' ;
FIRST_AI       : 'first_ai' ;

SPAN_AND     : '&&' ;
SPAN_OR      : '||' ;
SPAN_DIRECT  : '=>' ;
SPAN_INDIRECT: '->' ;
PIPE     : '|' ;
LBRACE   : '{' ;
RBRACE   : '}' ;
LPAREN   : '(' ;
RPAREN   : ')' ;
COMMA    : ',' ;
DOT      : '.' ;
EQ       : '=' ;
NEQ      : '!=' ;
GTE      : '>=' ;
LTE      : '<=' ;
GT       : '>' ;
LT       : '<' ;
PLUS     : '+' ;
MINUS    : '-' ;
STAR     : '*' ;
SLASH    : '/' ;

// String: single-quoted, supports \' escape
STRING_LITERAL : '\'' (~['\\\r\n] | '\\' .)* '\'' ;

// String: double-quoted, supports \" escape
DOUBLE_STRING_LITERAL : '"' (~["\\\r\n] | '\\' .)* '"' ;

// Number: non-negative; use MINUS NUMBER for negatives
NUMBER   : [0-9]+ ('.' [0-9]+)? ;

// Identifier: letters / underscore / digits, no dots (dots handled by 'field' rule)
IDENTIFIER : [a-zA-Z_][a-zA-Z0-9_]* ;

WS : [ \t\r\n]+ -> skip ;
