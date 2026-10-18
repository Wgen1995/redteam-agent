# 出处:人工构造(依据 CWE-327 MD5 口令哈希)
stored = hashlib.md5(password.encode()).hexdigest()
user.pw_hash = stored
