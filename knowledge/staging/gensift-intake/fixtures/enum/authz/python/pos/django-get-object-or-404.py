# 出处:人工构造(依据 CWE-639 get_object_or_404 快捷直查形态)
def invoice(request, invoice_id):
    obj = get_object_or_404(Invoice, pk=invoice_id)
    return JsonResponse({"total": obj.total})
