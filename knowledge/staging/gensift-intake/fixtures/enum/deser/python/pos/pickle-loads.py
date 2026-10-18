# 出处:人工构造(依据 CWE-502 pickle.loads 字节串形态——常接 b64decode 透传)
state = pickle.loads(base64.b64decode(request.data))
