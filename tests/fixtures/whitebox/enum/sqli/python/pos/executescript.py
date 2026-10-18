# 出处:人工构造(CWE-89 executescript)
cur.executescript("DELETE FROM t; INSERT INTO t VALUES ('" + u + "')")
