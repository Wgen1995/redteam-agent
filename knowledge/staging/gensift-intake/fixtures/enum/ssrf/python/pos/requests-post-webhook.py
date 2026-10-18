# 出处:人工构造(依据 CWE-918 requests webhook 形态)
def notify(webhook_url, message):
    r = requests.post(webhook_url, json={"text": message})
    return r.status_code
