// 出处:人工构造(硬负例:XPath 求值)
nodes = xp.evaluate("/orders/item[@sku='" + sku + "']", doc, XPathConstants.NODESET);
