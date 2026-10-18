# 出处:人工构造(依据 CWE-613 重置令牌无有效期,发出后永不失效)
def password_reset(user, token):
    reset_token = token
    if reset_token in issued_tokens:
        user.set_password(new_password)
        return True
    return False
