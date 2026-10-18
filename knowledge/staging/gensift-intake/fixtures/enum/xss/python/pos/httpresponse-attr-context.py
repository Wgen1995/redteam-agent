# 出处:人工构造(依据 CWE-79 属性上下文未加引号)
return HttpResponse(f'<a title={query} href=/s?q={query}>')
