// 出处: INV-002 阴性边界邻接——退款按业务规则显式回滚核销（有审计）
public void refund(String couponCode, String reason) {
  couponRepo.markUnused(couponCode);
  auditRepo.append("coupon-rollback", couponCode, reason);
}
