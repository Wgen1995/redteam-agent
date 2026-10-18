# 出处:人工构造(依据 CWE-89 二阶:配置存储 get_by_key 回读再拼接)
sql = "DELETE FROM token WHERE tag = '" + cfg_store.get_by_key(key).value + "'"
cur.execute(sql)
