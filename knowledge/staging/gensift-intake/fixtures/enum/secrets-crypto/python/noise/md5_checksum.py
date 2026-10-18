# 出处:人工构造(噪音:MD5 作文件校验和——允许命中)
h = hashlib.md5()
for chunk in iter(lambda: f.read(65536), b""):
    h.update(chunk)
checksum = h.hexdigest()
