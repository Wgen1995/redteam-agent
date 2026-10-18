// 出处:人工构造(硬负例:SpEL 表达式求值)
Object v = parser.parseExpression("#{body.price * 0.9}").getValue(ctx);
