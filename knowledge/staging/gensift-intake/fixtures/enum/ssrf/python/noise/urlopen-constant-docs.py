# 出处:人工构造(噪音:同 API 安全用法——常量 URL,允许命中)
def load_robots():
    return urllib.request.urlopen("https://example.com/robots.txt").read()
