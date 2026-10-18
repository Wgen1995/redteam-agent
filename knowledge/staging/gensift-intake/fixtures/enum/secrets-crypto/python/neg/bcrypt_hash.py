# 出处:人工构造(硬负例:慢哈希)
stored = bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12))
