# 出处:人工构造(硬负例:模板渲染无数据访问)
def page(request):
    return render(request, "billing/list.html", {"rows": rows})
