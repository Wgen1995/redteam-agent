# 出处:人工构造(依据 CWE-89 二阶:f-string 插回读对象字段——Python 次级载体)
cur.execute(f"SELECT * FROM cfg WHERE v = '{user.nickname}'")
