# 出处:人工构造(CWE-89 SQLAlchemy text 拼接)
rows = session.execute(text("SELECT * FROM t WHERE id = " + tid))
