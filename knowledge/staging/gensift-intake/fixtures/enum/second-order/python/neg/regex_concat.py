# 出处:人工构造(硬负例:正则编译拼接非回读)
pat = re.compile("^" + prefix + "$")
return pat.search(text)
