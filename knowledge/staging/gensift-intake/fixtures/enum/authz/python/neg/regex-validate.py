# 出处:人工构造(硬负例:格式校验)
ok = re.fullmatch(r"[a-z]{2}-[A-Z]{2}", locale_code) is not None
