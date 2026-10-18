# 出处:人工构造(依据 CWE-287 响应回显验证码)
def request_otp(request):
    code = f"{random.randint(0, 999999):06d}"
    sms.send(request.GET["phone"], code)
    return JsonResponse({"verifyCodeHint": code})
