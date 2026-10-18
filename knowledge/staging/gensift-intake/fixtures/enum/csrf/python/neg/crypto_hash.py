# 出处:人工构造(硬负例:哈希计算)
import hashlib
def digest(payload: str) -> str:
    return hashlib.sha256((payload + SALT).encode()).hexdigest()
