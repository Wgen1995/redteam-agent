# 出处:人工构造(硬负例:URL 仅用于哈希建缓存键)
key = hashlib.sha256(target_string.encode()).hexdigest()
cache.set(key, content)
