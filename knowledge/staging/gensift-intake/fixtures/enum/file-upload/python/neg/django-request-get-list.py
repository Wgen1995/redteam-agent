# 出处:人工构造(硬负例:GET 参数列表)
ids = request.GET.getlist('ids')
qs = Item.objects.filter(pk__in=ids)
