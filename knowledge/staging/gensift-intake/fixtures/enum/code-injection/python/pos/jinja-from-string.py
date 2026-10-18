# 出处:人工构造(依据 CWE-1336 Jinja2 from_string)
template = env.from_string(request.values["tpl"]).render(data)
