# 出处:人工构造(硬负例:对象级属主校验属 authz 类)
def invoice_detail(request, invoice_id):
    inv = get_object_or_404(Invoice, id=invoice_id)
    if inv.owner_id != request.user.id:
        raise Http404
    return render(request, "invoice.html", {"invoice": inv})
