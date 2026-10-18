# 出处:人工构造(依据 CWE-639 Django objects.get 按 id 直查无属主过滤形态)
def show(request):
    post = Post.objects.get(pk=request.GET["pid"])
    return render(request, "post.html", {"post": post})
