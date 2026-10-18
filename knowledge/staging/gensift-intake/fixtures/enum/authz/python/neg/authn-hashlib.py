# 出处:人工构造(硬负例:口令哈希是认证非授权)
def check_password(raw: str, stored: bytes) -> bool:
    digest = hashlib.pbkdf2_hmac("sha256", raw.encode(), stored[:16], 200_000)
    return hmac.compare_digest(digest, stored[16:])
