# 出处:人工构造(硬负例:urlparse 仅校验,无外发)
parts = urllib.parse.urlparse(candidate)
if parts.scheme != "https" or parts.hostname is None:
    raise ValueError("bad url")
