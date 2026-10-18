// 出处:人工构造(噪音:MD5 作缓存键——允许命中)
MessageDigest md = MessageDigest.getInstance("MD5");
String cacheKey = hex(md.digest(query.getBytes()));
