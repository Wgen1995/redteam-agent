// 出处: INV-002 核销 TOCTOU（检查与翻转两条独立语句）
public boolean redeem(String code) {
  Coupon c = couponRepo.findByCode(code);
  if (c.isUsed()) { return false; }
  paymentClient.capture(c.getAmount());
  c.setUsed(true);
  couponRepo.save(c);
  return true;
}
