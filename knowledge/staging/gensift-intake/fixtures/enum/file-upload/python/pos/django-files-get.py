# 出处:人工构造(依据 CWE-434 request.FILES.get 取文件原名落盘)
def avatar(request):
    f = request.FILES.get('avatar')
    if f is None:
        return HttpResponseBadRequest('missing')
    dest = os.path.join(MEDIA_ROOT, f.name)
    with open(dest, 'wb+') as out:
        out.write(f.read())
    return HttpResponse(dest)
