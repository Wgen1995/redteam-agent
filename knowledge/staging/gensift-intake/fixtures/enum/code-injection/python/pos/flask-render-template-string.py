# 出处:人工构造(依据 CWE-1336 Flask 字符串模板拼接)
return render_template_string("<p>Hello " + request.args.get("name") + "</p>")
