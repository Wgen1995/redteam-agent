# 出处:人工构造(依据 CWE-352 视图内 set_cookie 无 samesite 形态)
def subscribe(request):
    response = render(request, "subscribe.html")
    response.set_cookie("promo", request.POST.get("promo", ""))
    return response
