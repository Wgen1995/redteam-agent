// 出处:人工构造(依据 CVE-2025-69871 机制+CWE-362 检查-提交窗口,违反 INV-002)
public RedemptionResult redeemCoupon(RedeemCmd cmd) {
    Coupon c = couponRepository.findByCouponCode(cmd.getCode());   // 查 used 状态
    if (c == null) throw new NotFound("coupon");
    if (c.isUsed()) throw new Conflict("already used");
    Order o = orderRepository.findById(cmd.getOrderId()).orElseThrow();
    o.applyGift(c.getFaceValue());
    c.setUsed(true);                                                // 状态翻转:与检查两条独立语句
    couponRepository.save(c);
    orderRepository.save(o);
    return couponService.redeem(c, o);                              // 入账与检查非原子,并发重放双花
}
