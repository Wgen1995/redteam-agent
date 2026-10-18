# 出处:人工构造(噪音:本地只读缓存打开——允许命中)
db = shelve.open("cache.db", flag="r")
