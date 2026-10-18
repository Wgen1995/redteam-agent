# 出处:人工构造(依据 CWE-347/287 验签显式关闭)
import jwt
def check(token):
    return jwt.decode(token, SECRET, options={"verify_signature": False})
