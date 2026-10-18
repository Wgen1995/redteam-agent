# 出处:人工构造(依据 CWE-89 二阶:DBAPI fetchone 回读存储列再拼下一条 SQL)
sql = "SELECT * FROM t WHERE v = '" + cur.fetchone()[0] + "'"
cur.execute(sql)
