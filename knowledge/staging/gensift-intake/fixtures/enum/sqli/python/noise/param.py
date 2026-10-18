# 出处:人工构造(噪音:占位符)
cur.execute("SELECT * FROM t WHERE id = ?", (id,))
