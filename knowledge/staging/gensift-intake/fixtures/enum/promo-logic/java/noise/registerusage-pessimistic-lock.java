// 出处:人工构造(噪音:registerUsage 悲观锁兜底——锚在,符合 INV-001)
@Transactional
public void registerUsage(PromoUsageCmd cmd) {
    Promotion p = entityManager.find(Promotion.class, cmd.getPromoId(), LockModeType.PESSIMISTIC_WRITE);
    if (p.getUsed() >= p.getUsageLimit()) throw new Conflict("limit");
    p.setUsed(p.getUsed() + 1); // 检查与自增同锁同事务
    promotionRepository.save(p);
}
