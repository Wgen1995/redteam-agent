// 出处:人工构造(噪音:属主先查后删——检查与提交间留 TOCTOU 窗口,挂 bypass B6 hint)
public void cancel(Long orderId, Principal principal) {
    Order order = orderRepository.findById(orderId).orElseThrow();
    if (!order.getOwner().equals(principal.getName())) {
        throw new AccessDeniedException("not owner");
    }
    orderRepository.deleteById(orderId);
}
