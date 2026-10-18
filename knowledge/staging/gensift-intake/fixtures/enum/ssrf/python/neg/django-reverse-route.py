# 出处:人工构造(硬负例:reverse 反查内部路由名)
url = reverse("user-detail", args=[pk])
return JsonResponse({"location": url})
