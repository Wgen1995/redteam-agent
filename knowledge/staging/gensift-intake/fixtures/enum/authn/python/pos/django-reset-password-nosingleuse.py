# 出处:人工构造(依据 CWE-287 重置入口无一次性消费)
def reset_password(request):
    token = request.GET["token"]
    user = TokenStore.objects.get(token=token)
    user.set_password(request.POST["password"])
    user.save()
    return JsonResponse({"ok": True})
