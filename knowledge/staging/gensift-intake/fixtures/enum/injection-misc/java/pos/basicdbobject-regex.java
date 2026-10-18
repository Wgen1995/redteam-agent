// 出处:人工构造(依据 CWE-943 $regex 操作符注入)
BasicDBObject q = new BasicDBObject();
q.append("email", new BasicDBObject("$regex", req.getParameter("pattern")).append("$options", "i"));
users.find(q).limit(20);
