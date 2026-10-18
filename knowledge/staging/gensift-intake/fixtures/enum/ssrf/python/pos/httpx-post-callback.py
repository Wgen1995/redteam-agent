# 出处:人工构造(依据 CWE-918 httpx callback 形态)
def ping(callback, body):
    return httpx.post(callback, json=body).status_code
