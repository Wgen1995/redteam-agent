# 出处:人工构造(硬负例:DBAPI execute 属 sqli 域)
cur.execute("SELECT * FROM t WHERE id = ?", (user_id,))
