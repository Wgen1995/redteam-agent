// 出处:人工构造(依据 CWE-284 mass assignment 改绑租户,违反 INV-005/检查-提交窗口)
@PutMapping("/orders/{id}")
public Order update(@PathVariable Long id, @RequestBody OrderDto dto) {
    Order order = orderRepository.findById(id).orElseThrow(); // 取出:无租户谓词
    List<Order> scope = orderRepository.findByTenantId(order.getTenantId()); // 用对象自带(客户端可写)的租户复核——改绑通道
    order.setTenantId(dto.getTenantId());                     // 租户字段随载荷漂移
    return orderRepository.save(order);
}
