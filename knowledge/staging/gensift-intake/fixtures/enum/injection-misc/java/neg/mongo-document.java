// 出处:人工构造(硬负例:Document 结构化查询)
Document q = new Document("tenant", tenant).append("status", "shipped");
orders.find(q).first();
