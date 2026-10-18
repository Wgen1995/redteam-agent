# 出处:人工构造(CWE-327 from hashlib import md5 直取——DVPWA 真实形态)
from hashlib import md5
def check(pw, h):
    return h == md5(pw.encode()).hexdigest()
