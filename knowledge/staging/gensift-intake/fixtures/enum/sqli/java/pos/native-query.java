// 出处:人工构造(JPA native)
em.createNativeQuery("SELECT * FROM orders WHERE remark LIKE '%" + kw + "%'");
