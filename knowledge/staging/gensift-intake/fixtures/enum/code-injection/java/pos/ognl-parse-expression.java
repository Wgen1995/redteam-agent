// 出处:人工构造(依据 CWE-917 OGNL 表达式解析)
Object tree = Ognl.parseExpression(userExpr);
Object v = Ognl.getValue(tree, context, root);
