// 出处:人工构造(硬负例:缓存取值)
Object v = redisTemplate.opsForValue().get("user:" + id);
