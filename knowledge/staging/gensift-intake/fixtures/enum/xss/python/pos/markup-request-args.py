# 出处:人工构造(依据 CWE-79 MarkupSafe 标记安全绕过自动转义)
return Markup(request.args["html"])
