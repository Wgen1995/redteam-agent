# 出处:人工构造(噪音:常量 Location)
def session_expired(request):
    resp = HttpResponse(status=302)
    resp["Location"] = "/signin?expired=1"
    return resp
