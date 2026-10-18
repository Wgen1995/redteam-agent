# 出处:人工构造(噪音:钉死算法族与 exp 验证)
import jwt
def check(token):
    return jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"], options={"require": ["exp", "sub"]})
