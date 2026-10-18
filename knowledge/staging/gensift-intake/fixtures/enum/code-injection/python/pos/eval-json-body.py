# 出处:人工构造(依据 CWE-94 请求体 JSON 字段直达)
return eval(payload.get("expression"))
