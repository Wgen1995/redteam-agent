# 出处:人工构造(噪音:get_object_or_404 带属主条件)
def invoice(request, iid):
    obj = get_object_or_404(Invoice, pk=iid, author_id=request.user.pk)
    return JsonResponse({"total": obj.total})
