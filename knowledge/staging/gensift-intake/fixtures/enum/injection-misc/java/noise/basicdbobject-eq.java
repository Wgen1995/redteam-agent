// 出处:人工构造(噪音:结构化 append——允许命中)
BasicDBObject q = new BasicDBObject("status", statusValue);
q.append("region", "cn-north");
collection.find(q);
