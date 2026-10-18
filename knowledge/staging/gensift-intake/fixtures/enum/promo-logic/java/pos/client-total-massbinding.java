// 出处:人工构造(依据 CWE-840 信任边界,违反 INV-001/INV-004:客户端金额直达落库)
@PostMapping("/orders")
public Order create(@RequestBody OrderDto dto) {
    Order order = new Order();
    order.setItems(dto.getItems());
    order.setTotal(dto.getTotal());              // 客户端回传总价直接落库
    order.setPaid(dto.getDiscountedPrice());     // 折后价同样客户端可写
    pricingService.applyDiscount(order, dto.getDiscountAmount()); // 无服务端重算,直接采用传入折扣
    return orderRepository.save(order);
}
