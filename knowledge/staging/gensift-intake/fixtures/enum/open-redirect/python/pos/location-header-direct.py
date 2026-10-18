# 出处:人工构造(依据 CWE-601 response["Location"] 直写)
def go(request):
    resp = HttpResponse(status=302)
    resp["Location"] = request.GET["url"]
    return resp
