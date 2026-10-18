// 出处:人工构造(依据 CWE-362 读-改-写三段分离,违反 INV-001/INV-014)
public ClaimResult claim(Long templateId) {
    PromoTemplate t = templateRepository.findById(templateId).orElseThrow();
    if (t.getUsageCount() >= t.getTotalQuota()) {        // 读
        throw new Conflict("quota exhausted");
    }
    t.setUsageCount(t.getUsageCount() + 1);              // 改:非原子,并发领取超发
    templateRepository.save(t);
    return issueCoupon(t);
}
