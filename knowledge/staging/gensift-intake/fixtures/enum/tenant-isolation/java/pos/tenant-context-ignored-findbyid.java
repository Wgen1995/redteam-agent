// 出处:人工构造(依据 CWE-668 上下文在手但直查缺谓词,违反 INV-005)
@GetMapping("/orders/{id}")
public Order detail(@PathVariable Long id) {
    Long current = tenantContext.currentTenant(); // 上下文可用
    return orderRepository.findById(id).orElseThrow(); // 但详情直查:无 tenant 谓词
}
@GetMapping("/orders")
public List<Order> mine() {
    return orderRepository.findByTenantId(tenantContext.currentTenant()); // 列表带谓词——family 内不一致(点状缺失)
}
