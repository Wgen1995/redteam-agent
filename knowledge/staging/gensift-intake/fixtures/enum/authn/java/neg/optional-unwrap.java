// 出处:人工构造(硬负例:Optional 解包默认值)
public Plan resolvePlan(String tier) {
    return planRepository.findActive(tier).orElse(Plan.BASIC);
}
