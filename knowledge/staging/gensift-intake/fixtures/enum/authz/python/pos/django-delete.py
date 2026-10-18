# 出处:人工构造(依据 CWE-639 Django 按 id 删除无属主校验形态)
def remove_comment(request):
    Comment.objects.filter(pk=request.GET["cid"]).delete()
    return HttpResponse(status=204)
