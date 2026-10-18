# 出处:人工构造(硬负例:正则校验 URL 形态,无外发)
SAFE_URL = re.compile(r"^https://[a-z0-9.-]+\.example\.com(/.*)?$")
if not SAFE_URL.match(input_url):
    raise ValueError("bad url")
