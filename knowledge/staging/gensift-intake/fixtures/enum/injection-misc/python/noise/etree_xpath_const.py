# 出处:人工构造(噪音:编译常量——允许命中)
find_rows = etree.XPath("/config/defaults/maxRows")
return int(find_rows(doc)[0].text)
