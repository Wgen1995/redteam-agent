// 出处:人工构造(依据 CWE-639 JPA remove 形态)
public void purge(Long subscriptionId) {
    Subscription managed = entityManager.find(Subscription.class, subscriptionId);
    entityManager.remove(managed);
}
