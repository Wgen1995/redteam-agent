# 出处:人工构造(依据 CWE-1336 mako 字符串模板)
t = Template(user_template)
html = t.render(name=profile_name)
