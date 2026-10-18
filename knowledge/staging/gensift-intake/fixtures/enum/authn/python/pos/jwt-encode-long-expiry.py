# 出处:人工构造(依据 CWE-613 超长有效期签发)
import jwt
from datetime import timedelta
def issue_access(user):
    return jwt.encode({"sub": user.id}, SECRET, algorithm="HS256", expires_delta=timedelta(days=90))
