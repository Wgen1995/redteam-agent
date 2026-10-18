# 出处:人工构造(依据 CWE-643 etree.XPath 编译拼接)
find_user = etree.XPath("//order[@id='" + order_id + "']/total")
return find_user(doc)
