// 出处:人工构造(噪音:工厂+常量编译——允许命中)
XPathFactory f = XPathFactory.newInstance();
XPathExpression e = f.newXPath().compile("/config/defaults/maxRows");
return e.evaluate(doc);
