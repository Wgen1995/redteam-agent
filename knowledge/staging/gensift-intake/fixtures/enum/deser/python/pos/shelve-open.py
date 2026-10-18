# 出处:人工构造(依据 CWE-502 shelve 底层 pickle 载荷形态——上传路径可控)
db = shelve.open(upload_path)
val = db["k"]
