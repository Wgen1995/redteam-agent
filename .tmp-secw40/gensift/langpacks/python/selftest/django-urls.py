# selftest 样本: Django URL 路由 + request 取参共现标记（P-SRC08/P-SRC09/P-SRC10/P-SRC11/P-SRC12 预期命中）
from django.urls import path, re_path

urlpatterns = [
    path("orders/<int:order_id>/", views.order_detail),
    re_path(r"^reports/(?P<slug>[-a-z]+)/$", views.report),
]

def order_detail(request, order_id):
    name = request.GET.get("name")
    payload = request.body
    return views.render_detail(request.POST, payload)
