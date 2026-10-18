# 出处:人工构造(依据 CWE-79 Jinja safe 过滤器)
return render_template_string("{{ bio|safe }}", bio=request.args["bio"])
