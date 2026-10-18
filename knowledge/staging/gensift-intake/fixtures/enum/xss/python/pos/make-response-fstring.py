# 出处:人工构造(依据 CWE-79 反射型 f-string 拼 HTML,Flask)
return make_response(f"<h1>Results for {request.args.get('q')}</h1>")
