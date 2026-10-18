# 出处:人工构造(噪音:同 API 安全用法——常量 URL,允许命中,FP-1 参考)
def health():
    return requests.get("http://127.0.0.1:8080/health", timeout=2).ok
