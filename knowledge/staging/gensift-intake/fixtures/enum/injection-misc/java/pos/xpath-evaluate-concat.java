// 出处:人工构造(依据 CWE-643 XPath 表达式拼接)
XPathFactory factory = XPathFactory.newInstance();
XPath xpath = factory.newXPath();
Node node = (Node) xpath.evaluate("/users/user[@name='" + req.getParameter("name") + "']", doc, XPathConstants.NODE);
