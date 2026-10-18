// 出处:人工构造(依据 CWE-94 SpEL 全能力上下文)
StandardEvaluationContext ctx = new StandardEvaluationContext(bean);
parser.parseExpression("@bean runtime").getValue(ctx);
