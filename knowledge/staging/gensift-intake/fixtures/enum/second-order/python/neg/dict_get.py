# 出处:人工构造(硬负例:dict.get 拼接,非缓存回读)
v = d.get("k", "") + suffix
return v
