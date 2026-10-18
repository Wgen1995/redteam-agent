# 出处:人工构造(噪音:secrets 强熵源+短时效+一次性)
import secrets
def issue_reset_token():
    reset_token = secrets.token_urlsafe(32)
    store.set(reset_token, TTL_15MIN, single_use=True)
    return reset_token
