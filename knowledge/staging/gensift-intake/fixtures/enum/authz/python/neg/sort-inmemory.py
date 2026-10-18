# 出处:人工构造(硬负例:内存排序聚合)
ordered = sorted(rows, key=lambda r: r["created_at"], reverse=True)
