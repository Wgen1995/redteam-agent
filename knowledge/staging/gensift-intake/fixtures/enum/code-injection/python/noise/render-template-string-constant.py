# 出处:人工构造(噪音:字面量模板,变量经自动转义)
return render_template_string("<p>{{ title }}</p>", title=doc_title)
