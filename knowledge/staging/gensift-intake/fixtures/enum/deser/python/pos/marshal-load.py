# 出处:人工构造(依据 CWE-502 marshal.load 字节码对象形态)
obj = marshal.load(open(cache_file, "rb"))
