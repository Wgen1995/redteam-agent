// 出处:人工构造(依据 CWE-943 Map 键注入)
Map<String, Object> spec = new HashMap<>();
spec.put("$where", "this.price < " + req.getParameter("cap"));
FindIterable<Document> rs = products.find(new BasicDBObject(spec));
