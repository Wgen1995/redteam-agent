// 出处: INV-001 用量检查与登记非原子（无唯一约束/锁兜底）
public PromoResult apply(String promoId, String userId) {
  long used = promoRepo.countUsed(promoId);
  if (used >= promo.getCap()) { return PromoResult.CAPPED; }
  promoRepo.insertUsage(promoId, userId);
  return PromoResult.OK;
}
