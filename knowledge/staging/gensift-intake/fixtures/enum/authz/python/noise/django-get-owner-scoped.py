# 出处:人工构造(噪音:属主列进查询条件——允许命中,由五步判别,见 classes/fixture-spec.md §2)
def show(request, pid):
    post = Post.objects.get(pk=pid, owner=request.user)
    return render(request, "post.html", {"post": post})
