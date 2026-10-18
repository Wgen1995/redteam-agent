# 出处:人工构造(依据 CWE-94 f-string 拼接进 exec)
exec(f"configure({tenant}, {mode})")
