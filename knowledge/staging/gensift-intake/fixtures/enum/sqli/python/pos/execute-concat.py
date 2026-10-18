# 出处:人工构造(CWE-89 DBAPI 拼接)
cur.execute("SELECT * FROM t WHERE id = " + id)
