// 出处:人工构造(依据 CWE-643 工厂编译拼接)
XPath x = XPathFactory.newInstance().newXPath();
XPathExpression e = x.compile("/config/tenant[@code='" + tenantCode + "']/flag");
return e.evaluate(dom);
