# selftest 样本: DRF ViewSet 方法入口 + @api_view + request.data（P-SRC04..07/P-SRC13/P-SRC14 预期命中）
class OrderViewSet(viewsets.ModelViewSet):
    def list(self, request):
        return Response(self.get_queryset())

    def get_queryset(self):          # 弱锚同形命中: 非入口方法, 判据排除
        return Order.objects.all()

    def post_validate(self, request):
        return Response({})

    def put_confirm(self, request):
        return Response({})

    def delete_purge(self, request):
        return Response({})


@api_view(["POST"])
def sync(request):
    payload = request.data
    return Response(payload)
