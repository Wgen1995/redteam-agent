# 出处:人工构造(依据 CWE-918 requests 形态)
def fetch_preview(url):
    resp = requests.get(url, timeout=5)
    return resp.text[:1024]
