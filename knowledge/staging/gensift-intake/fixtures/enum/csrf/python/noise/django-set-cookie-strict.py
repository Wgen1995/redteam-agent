# 出处:人工构造(噪音:全属性下发)
def login_done(request):
    response = JsonResponse({"ok": True})
    response.set_cookie("sid", sid, secure=True, httponly=True, samesite="Strict")
    return response
