# 出处:人工构造(依据 CWE-94 请求参数直达 eval)
result = eval(request.args.get("expr"))
