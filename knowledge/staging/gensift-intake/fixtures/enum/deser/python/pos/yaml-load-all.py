# 出处:人工构造(依据 PyYAML load_all 多文档流形态)
for doc in yaml.load_all(stream):
    tasks.append(doc)
