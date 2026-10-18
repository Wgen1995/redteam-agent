// 出处:人工构造(依据 CWE-94 SpEL 表达式解析,SpEL 独立类二期先收形态)
Expression exp = parser.parseExpression(userFilter);
Object v = exp.getValue(ctx);
