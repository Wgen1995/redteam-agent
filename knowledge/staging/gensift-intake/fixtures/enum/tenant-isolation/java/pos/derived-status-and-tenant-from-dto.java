// 出处:人工构造(依据 CWE-284 派生查询谓词值取自 DTO,违反 INV-005)
@GetMapping("/orders/by-status")
public List<Order> byStatus(@RequestBody OrderQueryDto q) {
    return orderRepository.findByStatusAndTenantId(q.getStatus(), q.getTenantId()); // 谓词在,租户值来自请求体
}
