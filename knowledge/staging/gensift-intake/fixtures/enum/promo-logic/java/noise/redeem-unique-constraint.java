// 出处:人工构造(噪音:redeem 有唯一约束兜底——锚在,由五步判别,见 classes/fixture-spec.md §2,符合 INV-002)
@Transactional
public RedemptionResult redeem(RedeemCmd cmd) {
    Coupon c = couponRepository.findByCouponCode(cmd.getCode());
    if (c.isUsed()) throw new Conflict("used");
    // DDL: UNIQUE(coupon_id, order_id) 冲突即整体回滚——兜底成立
    couponUsageRepository.insertAndBind(c.getId(), cmd.getOrderId());
    c.setUsed(true);
    couponRepository.save(c);
    return couponService.redeem(c, cmd.getOrderId());
}
