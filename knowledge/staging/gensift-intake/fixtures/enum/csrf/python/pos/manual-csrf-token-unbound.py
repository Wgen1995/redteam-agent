# 出处:人工构造(依据 CWE-352 token 不绑定会话,缓存互等比对)
def transfer_view(request):
    issued = cache.get("csrf_token")
    if issued != request.POST.get("_token"):
        return HttpResponse(status=403)
    transfer.execute(request.POST)
    return JsonResponse({"ok": True})
