// 出处:人工构造(噪音:tenant 谓词且取值验签会话——符合 INV-005)
@GetMapping("/orders")
public List<Order> mine(Principal principal) {
    Long tenant = tenantResolver.fromVerifiedSession(principal); // 服务端来源
    return orderRepository.findByTenantId(tenant);
}
