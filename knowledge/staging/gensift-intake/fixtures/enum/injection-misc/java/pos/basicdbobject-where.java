// 出处:人工构造(依据 CWE-943 legacy BasicDBObject $where)
BasicDBObject query = new BasicDBObject();
query.append("$where", "this.tenant === '" + tenant + "'");
FindIterable<Document> rs = orders.find(query);
