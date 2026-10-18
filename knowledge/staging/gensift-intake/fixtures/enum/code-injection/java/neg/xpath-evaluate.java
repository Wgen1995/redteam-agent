// 出处:人工构造(硬负例:XPath evaluate 非 eval)
Object n = xp.evaluate("/root/item[@id='" + id + "']", doc, XPathConstants.NODE);
