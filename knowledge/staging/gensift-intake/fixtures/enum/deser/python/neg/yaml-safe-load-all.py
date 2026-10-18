# 出处:人工构造(硬负例:safe_load_all 多文档安全读)
for doc in yaml.safe_load_all(f):
    docs.append(doc)
