// 出处:CVE-2025-69871(MedusaJS v2.12.2 registerUsage 检查-自增非原子,并发 checkout 绕过促销用量上限,违反 INV-001)
public void onCheckout(PromoCmd cmd) {
    Promotion p = promotionRepository.findById(cmd.getPromoId()).orElseThrow();
    if (p.getUsageLimit() != null && p.getUsed() >= p.getUsageLimit()) {
        throw new Conflict("limit reached");
    }
    // 检查与自增之间无锁/无事务边界:并发请求全部通过检查
    p.setUsed(p.getUsed() + 1);
    promotionRepository.save(p);
    promotionEngine.registerUsage(cmd.getPromoId(), cmd.getOrderId()); // 登记与检查分离
}
