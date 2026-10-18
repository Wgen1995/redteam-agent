# 出处:人工构造(依据 CWE-434 工具类封装形态)
def handle_upload(request):
    for key in request.FILES:
        f = request.FILES[key]
        out = open(os.path.join(UPLOAD_DIR, f.name), 'wb')
        for chunk in f.chunks():
            out.write(chunk)
        out.close()
    return len(request.FILES)
