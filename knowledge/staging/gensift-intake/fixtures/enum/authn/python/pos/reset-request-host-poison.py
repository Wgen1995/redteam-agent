# 出处:人工构造(依据 CWE-287 密码重置毒化:Host 头进链接,PortSwigger 密码重置毒化同型)
def password_reset_request(request):
    email = request.POST["email"]
    host = request.get_host()
    link = f"https://{host}/reset?token={issue(email)}"
    send_mail("reset", link, recipient=email)
    return JsonResponse({"ok": True})
