# 出处:人工构造(噪音:回读值作绑定参数——安全用法,弱锚不命中)
cur.execute("SELECT * FROM t WHERE u = ?", (cfg_store.get_by_key(key).value,))
