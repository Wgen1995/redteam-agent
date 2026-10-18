// 出处:人工构造(硬负例:JPA Criteria 结构化)
CriteriaBuilder cb = em.getCriteriaBuilder();
cq.select(root).where(cb.equal(root.get("n"), v));
