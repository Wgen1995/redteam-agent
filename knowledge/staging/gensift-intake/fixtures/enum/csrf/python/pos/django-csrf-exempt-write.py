# 出处:人工构造(依据 CWE-352 豁免装饰器下的写视图——点状缺失)
from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def webhook_update(request):
    payload = json.loads(request.body)
    Setting.objects.filter(id=payload["id"]).update(value=payload["value"])
    return JsonResponse({"ok": True})
