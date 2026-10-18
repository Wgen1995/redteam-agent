# 出处:人工构造(依据 CWE-601 SSO 出口 relay 解码直跳)
from urllib.parse import unquote
def sso_exit(request):
    relay = request.GET.get("relayState", "")
    inner = unquote(relay)
    return HttpResponseRedirect(inner)
