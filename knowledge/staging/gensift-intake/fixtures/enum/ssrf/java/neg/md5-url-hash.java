// 出处:人工构造(硬负例:URL 仅用于哈希建缓存键)
byte[] digest = MessageDigest.getInstance("MD5").digest(targetString.getBytes(StandardCharsets.UTF_8));
String cacheKey = Hex.encodeHexString(digest);
cache.put(cacheKey, content);
