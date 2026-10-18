# 出处:人工构造(硬负例:参数化查询)
cur.execute("SELECT * FROM t WHERE id = ?", (id,))
