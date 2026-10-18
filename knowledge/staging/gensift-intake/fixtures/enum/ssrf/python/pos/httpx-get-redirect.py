# 出处:人工构造(依据 CWE-918 httpx follow_redirects 形态)
def resolve(target):
    r = httpx.get(target, follow_redirects=True)
    return r.text
