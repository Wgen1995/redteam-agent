# 出处:人工构造(噪音:同 API 安全用法——服务端生成存储名;允许命中)
from django.core.files.storage import default_storage

def invoice(request):
    f = request.FILES['invoice']
    stored = default_storage.save(f'{uuid4().hex}.pdf', f)
    return JsonResponse({'key': stored})
