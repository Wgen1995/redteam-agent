# 出处:人工构造(依据 CWE-79 存储型:昵称落库回显,Django)
return HttpResponse("<div class=nick>" + row["nickname"] + "</div>")
