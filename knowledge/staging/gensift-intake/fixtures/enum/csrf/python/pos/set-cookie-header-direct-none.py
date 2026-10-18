# 出处:人工构造(依据 CWE-352 头常量直写拼 SameSite=None 值)
SET_COOKIE = "Set-Cookie"
def sso_landing(request):
    value = sso.exchange(request.GET["code"])
    return HttpResponse(headers={SET_COOKIE: f"sid={value}; Path=/; SameSite=None"})
