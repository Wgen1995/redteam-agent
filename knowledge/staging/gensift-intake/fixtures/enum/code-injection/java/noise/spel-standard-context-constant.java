// 出处:人工构造(噪音:全能力上下文+常量表达式)
StandardEvaluationContext ctx = new StandardEvaluationContext(root);
Object v = parser.parseExpression("amount * 2").getValue(ctx);
