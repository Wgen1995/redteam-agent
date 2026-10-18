# 出处:人工构造(依据 CWE-330/327 弱随机令牌)
token = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
reset.link = f"/reset?token={token}"
