# 出处:人工构造(硬负例:字典推导)
visible = {k: v for k, v in payload.items() if k in ALLOWED}
