# 出处:人工构造(依据 CWE-330/287 random.choice 弱熵源令牌)
import random, string
def issue_reset_token():
    reset_token = "".join(random.choice(string.ascii_letters) for _ in range(8))
    issued.add(reset_token)
    return reset_token
