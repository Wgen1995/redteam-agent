# 出处:人工构造(依据 CWE-601 登出 next 直跳)
def logout_view(request):
    auth.logout(request)
    next_url = request.GET.get("next")
    return HttpResponseRedirect(next_url if next_url else "/")
