# 出处:人工构造(噪音:同 API + host 白名单形态——允许命中,Verifier 判据 C3 参考)
ALLOWED_HOSTS = {"img.example.com", "cdn.example.com"}
def guarded(user_url):
    host = urllib.parse.urlparse(user_url).hostname
    if host not in ALLOWED_HOSTS:
        raise PermissionError("host not allowed")
    return requests.get(user_url, timeout=3).content
