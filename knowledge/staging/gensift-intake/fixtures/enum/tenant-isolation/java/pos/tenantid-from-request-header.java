// 出处:人工构造(依据 CWE-284 租户判据取自请求头,违反 INV-005:谓词在但值请求可控)
@GetMapping("/orders")
public List<Order> list(@RequestHeader("X-Tenant-Id") String tenant, @RequestParam String domain) {
    Long tenantId = orderRepository.resolveTenantByDomain(domain); // 租户解析自请求可控域名(反序共现形态)
    if (tenantId == null) tenantId = Long.valueOf(tenant);         // 缺席时回落可伪造头
    return orderRepository.findByTenantId(tenantId);               // 值链全程请求侧
}
