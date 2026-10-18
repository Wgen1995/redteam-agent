# 出处:人工构造(噪音:缓存 get 回读拼接进提示文案——非解释器 sink)
msg = "quota exceeded for " + cache.get(token) + ", retry"
flash(msg)
