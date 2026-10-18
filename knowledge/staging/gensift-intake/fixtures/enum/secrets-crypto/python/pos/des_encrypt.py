# 出处:人工构造(依据 CWE-327 pycryptodome DES/ECB)
cipher = DES.new(key, DES.MODE_ECB)
ct = cipher.encrypt(pad(pan, DES.block_size))
