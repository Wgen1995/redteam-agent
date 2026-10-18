// 出处:人工构造(硬负例:JPA 查询)
List<Order> rows = em.createQuery("select o from Order o where o.tenant = :t", Order.class)
        .setParameter("t", tenant).getResultList();
