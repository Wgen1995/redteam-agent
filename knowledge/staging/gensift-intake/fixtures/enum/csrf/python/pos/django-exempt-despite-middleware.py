# 出处:人工构造(依据 CWE-352 中间件在场但视图点状豁免)
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def legacy_delete(request, entry_id):
    Entry.objects.filter(id=entry_id).delete()
    return JsonResponse({"ok": True})
