# 出处:人工构造(CWE-89 executemany 拼接)
cur.executemany("INSERT INTO t VALUES ('" + v + "')", rows)
