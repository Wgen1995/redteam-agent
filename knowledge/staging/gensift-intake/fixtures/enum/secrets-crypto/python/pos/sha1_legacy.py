# 出处:人工构造(依据 CWE-327 SHA-1 遗留比对)
if hashlib.sha1(pin.encode()).hexdigest() == row["hash"]:
    grant_access()
