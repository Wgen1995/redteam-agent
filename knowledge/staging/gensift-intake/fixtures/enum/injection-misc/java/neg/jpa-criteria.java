// 出处:人工构造(硬负例:结构化 Criteria)
CriteriaBuilder cb = em.getCriteriaBuilder();
cq.select(root).where(cb.equal(root.get("sku"), sku));
