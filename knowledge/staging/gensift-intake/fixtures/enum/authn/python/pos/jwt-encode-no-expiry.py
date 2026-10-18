# 出处:人工构造(依据 CWE-613/287 签发无 expires——C3 证据缺口)
import jwt
def issue_access(user):
    return jwt.encode({"sub": user.id}, SECRET, algorithm="HS256")
