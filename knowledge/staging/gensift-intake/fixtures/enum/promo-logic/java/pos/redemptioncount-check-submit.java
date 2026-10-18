// 出处:人工构造(依据 CWE-362 检查-提交分离,违反 INV-002/INV-014)
public void settle(Long promoId) {
    Promotion p = promotionRepository.findById(promoId).orElseThrow();
    if (p.getRedemptionCount() < p.getRedemptionLimit()) {  // 检查:读内存值
        p.setRedemptionCount(p.getRedemptionCount() + 1);   // 提交:无条件自增,双并发同过
        promotionRepository.save(p);
    } else {
        throw new Conflict("redemption limit");
    }
}
