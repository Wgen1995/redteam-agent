# 出处:人工构造(噪音:同 API 安全用法——表单校验+服务端名;允许命中)
def avatar(request):
    form = AvatarForm(request.POST, request.FILES)
    if form.is_valid():
        f = request.FILES.get('avatar')
        name = f'{uuid4().hex}.img'
        with open(os.path.join(NONWEB_DIR, name), 'wb') as out:
            shutil.copyfileobj(f.file, out)
        form.save()
    return redirect('profile')
