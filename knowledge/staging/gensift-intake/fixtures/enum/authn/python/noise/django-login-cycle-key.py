# 出处:人工构造(噪音:登录后 cycle_key 轮换)
def login_view(request):
    user = auth.authenticate(request)
    if user is not None:
        auth.login(request, user)
        request.session.cycle_key()
        response = JsonResponse({"ok": True})
        response.set_cookie("sessionid", request.session.session_key, secure=True, httponly=True, samesite="Strict")
        return response
    return HttpResponse(status=401)
