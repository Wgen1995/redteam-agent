# 出处:人工构造(硬负例:Django 固定内部重定向)
def logout(request):
    return HttpResponseRedirect("/login/?next=/home")
