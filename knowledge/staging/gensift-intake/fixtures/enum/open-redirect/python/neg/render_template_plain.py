# 出处:人工构造(硬负例:模板渲染,django)
def profile_page(request):
    return render(request, "profile.html", {"profile": request.user.profile})
