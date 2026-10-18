// 出处:人工构造(依据 CWE-643 编译表达式拼接)
XPathExpression expr = xpath.compile("//order[@id='" + orderId + "']/total");
String total = expr.evaluate(doc);
