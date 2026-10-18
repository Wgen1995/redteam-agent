# 出处:人工构造(依据 CWE-434 default_storage.save 保留客户端名)
from django.core.files.storage import default_storage

def receive(request):
    f = request.FILES['invoice']
    stored = default_storage.save(f.name, f)
    return JsonResponse({'path': stored})
