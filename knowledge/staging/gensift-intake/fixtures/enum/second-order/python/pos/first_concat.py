# 出处:人工构造(依据 CWE-89 二阶:queryset first() 回读存储值再拼接)
sql = "UPDATE counters SET label = '" + session.query(Cfg).filter_by(k=key).first().val + "'"
cur.execute(sql)
