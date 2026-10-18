# 出处:人工构造(CWE-327 from hashlib import sha1 直取)
from hashlib import sha1
def fingerprint(data):
    return sha1(data).hexdigest()
