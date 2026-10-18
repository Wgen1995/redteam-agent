# 出处:人工构造(噪音:FP 卡形态——UUID 重命名+扩展白名单+非 web 目录;允许命中)
import uuid

ALLOWED_EXT = {'jpg', 'png', 'webp'}

def upload(request):
    f = request.FILES['file']
    ext = f.name.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return HttpResponseBadRequest('ext')
    stored = f'{uuid.uuid4().hex}.{ext}'
    with open(os.path.join(STORE_DIR, stored), 'wb') as out:
        for chunk in f.chunks():
            out.write(chunk)
    Meta.objects.create(original=f.name, stored=stored)
    return HttpResponse(stored)
