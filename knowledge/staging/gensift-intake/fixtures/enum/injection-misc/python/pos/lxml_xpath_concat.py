# 出处:人工构造(依据 CWE-643 etree.XPath 编译 %-格式化拼接)
find_user = etree.XPath("//user[@name='%s']" % request.args["name"])
return find_user(doc)
