# 出处:人工构造(噪音:常量目标)
def login_view(request):
    auth.authenticate(request)
    return HttpResponseRedirect("/dashboard")
