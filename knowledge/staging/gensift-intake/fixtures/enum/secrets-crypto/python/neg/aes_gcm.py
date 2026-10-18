# 出处:人工构造(硬负例:cryptography 库 AEAD)
ct = AESGCM(key).encrypt(nonce, plain, None)
