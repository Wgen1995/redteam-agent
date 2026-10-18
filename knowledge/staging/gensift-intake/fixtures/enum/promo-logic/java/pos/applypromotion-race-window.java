// 出处:人工构造(依据 CVE-2025-69871 同族竞态,违反 INV-013/INV-002)
@PostMapping("/cart/promo")
public Cart applyPromo(@RequestBody PromoDto dto) {
    Cart cart = cartRepository.findById(dto.getCartId()).orElseThrow();
    PromotionRule r = ruleRepository.findByCode(dto.getRuleCode()); // 规则读取
    if (ruleRepository.countActiveOn(cart.getId()) > 0) {
        throw new Conflict("promo already applied");      // 检查
    }
    cart.setRuleCode(r.getCode());                        // 提交:窗口内并发叠加多规则
    promotionRepository.save(r.usageSnapshot(cart));
    return pricingService.applyPromotion(cart.getId(), dto.getRuleCode()); // 各端各自算折扣
}
